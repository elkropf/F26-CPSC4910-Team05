-- MySQL dump 10.13  Distrib 9.6.0, for Win64 (x86_64)
--
-- Host: cpsc4910-f26.cobd8enwsupz.us-east-1.rds.amazonaws.com    Database: Team05_DB
-- ------------------------------------------------------
-- Server version	8.4.9

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `about_aboutproductinfo`
--

DROP TABLE IF EXISTS `about_aboutproductinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `about_aboutproductinfo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `team_number` varchar(3) NOT NULL,
  `product_name` varchar(100) NOT NULL,
  `product_description` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `about_aboutsprintinfo`
--

DROP TABLE IF EXISTS `about_aboutsprintinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `about_aboutsprintinfo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sprint_number` varchar(2) NOT NULL,
  `release_date` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_admin`
--

DROP TABLE IF EXISTS `accounts_admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `accounts_admin_user_id_af8a3aeb_fk` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_adminlog`
--

DROP TABLE IF EXISTS `accounts_adminlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_adminlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `admin_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_adminlog_admin_id_2cde89c5_fk_accounts_admin_id` (`admin_id`),
  CONSTRAINT `accounts_adminlog_admin_id_2cde89c5_fk_accounts_admin_id` FOREIGN KEY (`admin_id`) REFERENCES `accounts_admin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_application`
--

DROP TABLE IF EXISTS `accounts_application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_application` (
  `id` int NOT NULL AUTO_INCREMENT,
  `application_status` varchar(20) NOT NULL,
  `application_message` longtext NOT NULL,
  `submission_date` datetime(6) NOT NULL,
  `review_date` datetime(6) DEFAULT NULL,
  `driver_id` int NOT NULL,
  `organization_id` int DEFAULT NULL,
  `rejection_reason` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_driver_organization_application` (`driver_id`,`organization_id`),
  KEY `accounts_application_driver_id_6daebc23` (`driver_id`),
  KEY `accounts_application_organization_id_5c6d1fe1_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_application_driver_id_6daebc23_fk_accounts_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`),
  CONSTRAINT `accounts_application_organization_id_5c6d1fe1_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_auditlog`
--

DROP TABLE IF EXISTS `accounts_auditlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_auditlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_id` int DEFAULT NULL,
  `actor_role` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `organization_id` int DEFAULT NULL,
  `record_id` bigint unsigned DEFAULT NULL,
  `record_type` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_auditlog_user_id_1dfbca79_fk_accounts_user_id` (`user_id`),
  KEY `audit_org_time_idx` (`organization_id`,`timestamp`),
  KEY `audit_action_time_idx` (`action`,`timestamp`),
  CONSTRAINT `accounts_auditlog_organization_id_020a9dfc_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_auditlog_user_id_1dfbca79_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_auditlog_chk_1` CHECK ((`record_id` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=282 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_bulkimportjob`
--

DROP TABLE IF EXISTS `accounts_bulkimportjob`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_bulkimportjob` (
  `id` int NOT NULL AUTO_INCREMENT,
  `source_file` varchar(100) NOT NULL,
  `result_file` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `processed_rows` bigint unsigned NOT NULL,
  `successful_rows` bigint unsigned NOT NULL,
  `failed_rows` bigint unsigned NOT NULL,
  `error_message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `started_at` datetime(6) DEFAULT NULL,
  `finished_at` datetime(6) DEFAULT NULL,
  `uploaded_by_id` int NOT NULL,
  `organization_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_bulkimportj_uploaded_by_id_c1208776_fk_accounts_` (`uploaded_by_id`),
  KEY `accounts_bulkimportj_organization_id_fd869578_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_bulkimportj_organization_id_fd869578_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_bulkimportj_uploaded_by_id_c1208776_fk_accounts_` FOREIGN KEY (`uploaded_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_bulkimportjob_chk_1` CHECK ((`processed_rows` >= 0)),
  CONSTRAINT `accounts_bulkimportjob_chk_2` CHECK ((`successful_rows` >= 0)),
  CONSTRAINT `accounts_bulkimportjob_chk_3` CHECK ((`failed_rows` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_driver`
--

DROP TABLE IF EXISTS `accounts_driver`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_driver` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `accounts_driver_user_id_193e1fcf_fk` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_driverlog`
--

DROP TABLE IF EXISTS `accounts_driverlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_driverlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `driver_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_driverlog_driver_id_e962bce4_fk_accounts_driver_id` (`driver_id`),
  CONSTRAINT `accounts_driverlog_driver_id_e962bce4_fk_accounts_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_driverorganization`
--

DROP TABLE IF EXISTS `accounts_driverorganization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_driverorganization` (
  `id` int NOT NULL AUTO_INCREMENT,
  `joined_at` datetime(6) NOT NULL,
  `driver_id` int NOT NULL,
  `organization_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_driver_organization_membership` (`driver_id`,`organization_id`),
  KEY `accounts_driverorgan_organization_id_5ae7af19_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_driverorgan_driver_id_716c0999_fk_accounts_` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`),
  CONSTRAINT `accounts_driverorgan_organization_id_5ae7af19_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_mfachallenge`
--

DROP TABLE IF EXISTS `accounts_mfachallenge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_mfachallenge` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code_hash` varchar(128) NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `failed_attempts` smallint unsigned NOT NULL,
  `used_at` datetime(6) DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_mfachallenge_user_id_f2b3cda5_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `accounts_mfachallenge_user_id_f2b3cda5_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_mfachallenge_chk_1` CHECK ((`failed_attempts` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_notification`
--

DROP TABLE IF EXISTS `accounts_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_notification` (
  `id` int NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  `notification_type` varchar(30) NOT NULL,
  `organization_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_notification_user_id_30e6cfc5_fk_accounts_user_id` (`user_id`),
  KEY `accounts_notificatio_organization_id_d42c6c6e_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_notificatio_organization_id_d42c6c6e_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_notification_user_id_30e6cfc5_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_order`
--

DROP TABLE IF EXISTS `accounts_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_order` (
  `id` int NOT NULL AUTO_INCREMENT,
  `total_points` int unsigned NOT NULL,
  `order_status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `driver_id` int NOT NULL,
  `organization_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_order_driver_id_a64d7dfd_fk_accounts_driver_id` (`driver_id`),
  KEY `accounts_order_organization_id_21c811e7_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_order_driver_id_a64d7dfd_fk_accounts_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`),
  CONSTRAINT `accounts_order_organization_id_21c811e7_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_order_chk_1` CHECK ((`total_points` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_orderitem`
--

DROP TABLE IF EXISTS `accounts_orderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_orderitem` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `points_cost` int unsigned NOT NULL,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product_per_order` (`order_id`,`product_id`),
  KEY `accounts_orderitem_product_id_bbbf7843_fk_accounts_product_id` (`product_id`),
  CONSTRAINT `accounts_orderitem_order_id_890e34c7_fk_accounts_order_id` FOREIGN KEY (`order_id`) REFERENCES `accounts_order` (`id`),
  CONSTRAINT `accounts_orderitem_product_id_bbbf7843_fk_accounts_product_id` FOREIGN KEY (`product_id`) REFERENCES `accounts_product` (`id`),
  CONSTRAINT `accounts_orderitem_chk_1` CHECK ((`quantity` >= 0)),
  CONSTRAINT `accounts_orderitem_chk_2` CHECK ((`points_cost` >= 0)),
  CONSTRAINT `quantity_greater_than_zero` CHECK ((`quantity` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_organization`
--

DROP TABLE IF EXISTS `accounts_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_organization` (
  `id` int NOT NULL AUTO_INCREMENT,
  `organization_name` longtext NOT NULL,
  `organization_description` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `points_per_dollar` decimal(12,4) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_pointlog`
--

DROP TABLE IF EXISTS `accounts_pointlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_pointlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `points_changed` int NOT NULL,
  `action` longtext NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `driver_id` int NOT NULL,
  `organization_id` int NOT NULL,
  `changed_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_pointlog_driver_id_c016a324_fk_accounts_driver_id` (`driver_id`),
  KEY `accounts_pointlog_organization_id_9570b896_fk_accounts_` (`organization_id`),
  KEY `accounts_pointlog_changed_by_user_id_f88bdc3b_fk_accounts_` (`changed_by_user_id`),
  CONSTRAINT `accounts_pointlog_changed_by_user_id_f88bdc3b_fk_accounts_` FOREIGN KEY (`changed_by_user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_pointlog_driver_id_c016a324_fk_accounts_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`),
  CONSTRAINT `accounts_pointlog_organization_id_9570b896_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_points`
--

DROP TABLE IF EXISTS `accounts_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_points` (
  `id` int NOT NULL AUTO_INCREMENT,
  `points_balance` int unsigned NOT NULL,
  `last_updated` datetime(6) NOT NULL,
  `driver_id` int NOT NULL,
  `organization_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_driver_organization_points` (`driver_id`,`organization_id`),
  KEY `accounts_points_driver_id_b1968bfb` (`driver_id`),
  KEY `accounts_points_organization_id_46bc5c7c_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_points_driver_id_b1968bfb_fk_accounts_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `accounts_driver` (`id`),
  CONSTRAINT `accounts_points_organization_id_46bc5c7c_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_points_chk_1` CHECK ((`points_balance` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_product`
--

DROP TABLE IF EXISTS `accounts_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_product` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(255) NOT NULL,
  `product_description` longtext NOT NULL,
  `points_value` int unsigned NOT NULL,
  `instock_quantity` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `organization_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_product_organization_id_b1393e22_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_product_organization_id_b1393e22_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_product_chk_1` CHECK ((`points_value` >= 0)),
  CONSTRAINT `accounts_product_chk_2` CHECK ((`instock_quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_sponsor`
--

DROP TABLE IF EXISTS `accounts_sponsor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_sponsor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `organization_id` int DEFAULT NULL,
  `fee_percentage` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `accounts_sponsor_organization_id_a5f8b1ce_fk_accounts_` (`organization_id`),
  CONSTRAINT `accounts_sponsor_organization_id_a5f8b1ce_fk_accounts_` FOREIGN KEY (`organization_id`) REFERENCES `accounts_organization` (`id`),
  CONSTRAINT `accounts_sponsor_user_id_7ead2efa_fk` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_sponsorlog`
--

DROP TABLE IF EXISTS `accounts_sponsorlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_sponsorlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `sponsor_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_sponsorlog_sponsor_id_bc6a37e0_fk_accounts_sponsor_id` (`sponsor_id`),
  CONSTRAINT `accounts_sponsorlog_sponsor_id_bc6a37e0_fk_accounts_sponsor_id` FOREIGN KEY (`sponsor_id`) REFERENCES `accounts_sponsor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` longtext NOT NULL,
  `last_name` longtext NOT NULL,
  `email` longtext NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `user_type` varchar(20) NOT NULL,
  `order_notifications` tinyint(1) NOT NULL,
  `point_notifications` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_permissions_user_id_e4f0a161_fk` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-23  9:47:22
