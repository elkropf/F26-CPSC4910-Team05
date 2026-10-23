from uuid import uuid4
from django.db import DataError, IntegrityError, transaction
from .models import Driver, DriverOrganization, Organization, Sponsor, User, UserType, Points, pointLog


#report error for one row
class ImportRowError(Exception):
    pass


#find an account by email or create one with no usable password
def find_or_create_import_user(
    *,
    email,
    first_name,
    last_name,
    user_type,
):
    email = email.strip()

    if not email:
        raise ImportRowError("An email address is required.")

    if user_type not in (UserType.DRIVER, UserType.SPONSOR):
        raise ImportRowError("Only driver and sponsor accounts can be imported.")

    matches = list(
        User.objects.filter(email__iexact=email).order_by("id")[:2]
    )

    if len(matches) > 1:
        raise ImportRowError(
            "Multiple accounts use this email address."
        )

    if matches:
        user = matches[0]

        if user.user_type != user_type:
            raise ImportRowError(
                "This email belongs to an account with a different role."
            )

        if not user.is_active:
            raise ImportRowError(
                "This account is inactive and must be reviewed."
            )

        return user, False

    user = User.objects.create_user(
        username=f"import_{uuid4().hex}",
        email=email,
        first_name=first_name,
        last_name=last_name,
        user_type=user_type,
        password=None,
    )

    return user, True

#split file row into fields
def split_import_row(line):
    fields = line.rstrip("\r\n").split("|")
    record_type = fields[0]

    if record_type == "O":
        if len(fields) != 2 or not fields[1].strip():
            raise ImportRowError("Use O|organization name.")

        return {
            "type": "O",
            "organization_name": fields[1],
        }

    if record_type not in ("D", "S"):
        raise ImportRowError("Record type must be O, D, or S.")

    if not 5 <= len(fields) <= 7:
        raise ImportRowError("User rows require 5 to 7 fields.")

    fields += [""] * (7 - len(fields))

    return dict(zip(
        [
            "type", "organization_name", "first_name",
            "last_name", "email", "points", "reason",
        ],
        fields,
    ))

#optional point adjustment
def read_import_points(record):
    if not record["points"].strip():
        return None

    if not record["reason"].strip():
        raise ImportRowError("Points require a reason.")

    try:
        points = int(record["points"])
    except ValueError:
        raise ImportRowError("Points must be a whole number.")

    if not -2147483648 <= points <= 2147483647:
        raise ImportRowError("Points are outside the allowed range.")

    return points

#organization for driver or sponsor
def import_organization(record, uploader):
    warnings = []

    if uploader.user_type == UserType.SPONSOR:
        try:
            organization = uploader.sponsor.organization
        except Sponsor.DoesNotExist:
            raise ImportRowError("Sponsor profile not found.")

        if organization is None:
            raise ImportRowError("Sponsor profile is not linked to an organization.")

        if record["organization_name"]:
            warnings.append(
                "Organization name is ignored: using your organization."
            )
    elif uploader.user_type == UserType.ADMIN:
        matches = list(Organization.objects.filter(
            organization_name=record["organization_name"]
        )[:2])

        if len(matches) != 1:
            raise ImportRowError(
                "Organization name must match exactly one existing organization."
            )

        organization = matches[0]

    else:
        raise ImportRowError("Only sponsors and admins can import users.")

    if not organization.is_active:
        raise ImportRowError("Organization is inactive.")

    return organization, warnings

#create organization from admin's O record
def create_import_organization(record, uploader):
    if uploader.user_type != UserType.ADMIN:
        raise ImportRowError(
            "Only admins can import organizations."
        )

    name = record["organization_name"]

    if Organization.objects.filter(organization_name=name).exists():
        raise ImportRowError("An organization with this name already exists.")

    return Organization.objects.create(
        organization_name=name
    )

#create driver profile and accept their organization membership
def add_import_driver(user, organization):
    driver, _ = Driver.objects.get_or_create(user=user)

    membership, created = DriverOrganization.objects.get_or_create(
        driver=driver,
        organization=organization,
    )

    return driver, created

#create sponsor profile without moving an existing sponsor
def add_import_sponsor(user, organization):
    sponsor, created = Sponsor.objects.get_or_create(
        user=user,
        defaults={"organization": organization},
    )

    if not created:
        if sponsor.organization_id is None:
            sponsor.organization = organization
            sponsor.save(update_fields=["organization"])
        elif sponsor.organization_id != organization.id:
            raise ImportRowError(
                "This sponsor already belongs to another organization."
            )

    return sponsor, created

#update driver's organization balance and record who changed it
def apply_import_points(driver, organization, points, reason, uploader):
    if points is None or points == 0:
        return

    with transaction.atomic():
        Driver.objects.select_for_update().get(id=driver.id)

        balance, _ = Points.objects.select_for_update().get_or_create(
            driver=driver,
            organization=organization,
        )

        new_balance = balance.points_balance + points

        if not 0 <= new_balance <= 4294967295:
            raise ImportRowError(
                "The resulting points balance is outside the allowed range."
            )

        balance.points_balance = new_balance
        balance.save()

        pointLog.objects.create(
            driver=driver,
            organization=organization,
            changed_by_user=uploader,
            points_changed=points,
            action=reason,
        )

#process only one record and undo if fails
@transaction.atomic
def process_import_row(line, uploader):
    if not uploader.is_authenticated or not uploader.is_active:
        raise ImportRowError("An active signed-in account is required.")

    if uploader.user_type not in (UserType.SPONSOR, UserType.ADMIN):
        raise ImportRowError("Only sponsors and admins can import users.")

    record = split_import_row(line)

    if record["type"] == "O":
        organization = create_import_organization(record, uploader)
        return {
            "type": "O",
            "organization_id": organization.id,
            "created": True,
            "warnings": [],
        }

    organization, warnings = import_organization(record, uploader)
    is_driver = record["type"] == "D"

    points = read_import_points(record) if is_driver else None

    if not is_driver and (record["points"] or record["reason"]):
        warnings.append("Points and reason ignored for a sponsor account.")

    user, created = find_or_create_import_user(
        email=record["email"],
        first_name=record["first_name"],
        last_name=record["last_name"],
        user_type=UserType.DRIVER if is_driver else UserType.SPONSOR,
    )

    if is_driver:
        driver, _ = add_import_driver(user, organization)
        apply_import_points(
            driver, organization, points, record["reason"], uploader
        )
    else:
        add_import_sponsor(user, organization)

    return {
        "type": record["type"],
        "user_id": user.id,
        "organization_id": organization.id,
        "created": created,
        "warnings": warnings,
    }

#process each file line and return its result and dont stop on bad lines, just report them
def process_import_file(uploaded_file, uploader):
    for line_number, raw_line in enumerate(uploaded_file, start=1):
        try:
            line = (
                raw_line.decode("utf-8")
                if isinstance(raw_line, bytes)
                else raw_line
            )

            if line_number == 1:
                line = line.removeprefix("\ufeff")

            result = process_import_row(line, uploader)

        except UnicodeDecodeError:
            yield {
                "line": line_number,
                "status": "error",
                "error": "This line is not valid UTF-8 text.",
            }

        except ImportRowError as error:
            yield {
                "line": line_number,
                "status": "error",
                "error": str(error),
            }

        except (DataError, IntegrityError):
            yield {
                "line": line_number,
                "status": "error",
                "error": "This row conflicts with database constraints.",
            }

        else:
            yield {
                "line": line_number,
                "status": "success",
                **result,
            }