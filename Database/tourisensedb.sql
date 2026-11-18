-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: tourisense
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('0683d0e5d8fa');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attractions`
--

DROP TABLE IF EXISTS `attractions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attractions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_id` int NOT NULL,
  `name` varchar(150) NOT NULL,
  `slug` varchar(180) NOT NULL,
  `category` varchar(80) DEFAULT NULL,
  `description` text,
  `image_url` varchar(500) DEFAULT NULL,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `ticket_price` decimal(10,2) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_attractions_slug` (`slug`),
  KEY `ix_attractions_category` (`category`),
  KEY `ix_attractions_destination_active` (`destination_id`,`is_active`),
  KEY `ix_attractions_destination_id` (`destination_id`),
  KEY `ix_attractions_is_active` (`is_active`),
  CONSTRAINT `attractions_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attractions`
--

LOCK TABLES `attractions` WRITE;
/*!40000 ALTER TABLE `attractions` DISABLE KEYS */;
/*!40000 ALTER TABLE `attractions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `destinations`
--

DROP TABLE IF EXISTS `destinations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `destinations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `slug` varchar(180) NOT NULL,
  `city` varchar(120) NOT NULL,
  `state_region` varchar(120) NOT NULL,
  `country` varchar(120) NOT NULL,
  `category` varchar(80) NOT NULL,
  `description` text,
  `tagline` varchar(255) DEFAULT NULL,
  `best_time_to_visit` varchar(120) DEFAULT NULL,
  `budget_info` varchar(120) DEFAULT NULL,
  `rating` decimal(3,2) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_destinations_slug` (`slug`),
  KEY `ix_destinations_category` (`category`),
  KEY `ix_destinations_city` (`city`),
  KEY `ix_destinations_city_category` (`city`,`category`),
  KEY `ix_destinations_country` (`country`),
  KEY `ix_destinations_is_active` (`is_active`),
  KEY `ix_destinations_state_region` (`state_region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `destinations`
--

LOCK TABLES `destinations` WRITE;
/*!40000 ALTER TABLE `destinations` DISABLE KEYS */;
/*!40000 ALTER TABLE `destinations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hotels`
--

DROP TABLE IF EXISTS `hotels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hotels` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_id` int NOT NULL,
  `name` varchar(150) NOT NULL,
  `location` varchar(255) NOT NULL,
  `description` text,
  `price_per_night` decimal(10,2) DEFAULT NULL,
  `rating` decimal(3,2) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `amenities` text,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_hotels_destination_name` (`destination_id`,`name`),
  KEY `ix_hotels_destination_active` (`destination_id`,`is_active`),
  KEY `ix_hotels_destination_id` (`destination_id`),
  KEY `ix_hotels_is_active` (`is_active`),
  CONSTRAINT `hotels_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hotels`
--

LOCK TABLES `hotels` WRITE;
/*!40000 ALTER TABLE `hotels` DISABLE KEYS */;
/*!40000 ALTER TABLE `hotels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `itinerary_activities`
--

DROP TABLE IF EXISTS `itinerary_activities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `itinerary_activities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `itinerary_day_id` int NOT NULL,
  `activity_order` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `start_time` time DEFAULT NULL,
  `duration_minutes` int DEFAULT NULL,
  `cost` decimal(10,2) DEFAULT NULL,
  `attraction_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_itinerary_activities_day_order` (`itinerary_day_id`,`activity_order`),
  KEY `ix_itinerary_activities_attraction_id` (`attraction_id`),
  KEY `ix_itinerary_activities_day_attraction` (`itinerary_day_id`,`attraction_id`),
  KEY `ix_itinerary_activities_itinerary_day_id` (`itinerary_day_id`),
  CONSTRAINT `itinerary_activities_ibfk_1` FOREIGN KEY (`attraction_id`) REFERENCES `attractions` (`id`),
  CONSTRAINT `itinerary_activities_ibfk_2` FOREIGN KEY (`itinerary_day_id`) REFERENCES `itinerary_days` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `itinerary_activities`
--

LOCK TABLES `itinerary_activities` WRITE;
/*!40000 ALTER TABLE `itinerary_activities` DISABLE KEYS */;
/*!40000 ALTER TABLE `itinerary_activities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `itinerary_days`
--

DROP TABLE IF EXISTS `itinerary_days`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `itinerary_days` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trip_id` int NOT NULL,
  `day_number` int NOT NULL,
  `date` date DEFAULT NULL,
  `title` varchar(180) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_itinerary_days_trip_day` (`trip_id`,`day_number`),
  KEY `ix_itinerary_days_trip_id` (`trip_id`),
  CONSTRAINT `itinerary_days_ibfk_1` FOREIGN KEY (`trip_id`) REFERENCES `trips` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `itinerary_days`
--

LOCK TABLES `itinerary_days` WRITE;
/*!40000 ALTER TABLE `itinerary_days` DISABLE KEYS */;
/*!40000 ALTER TABLE `itinerary_days` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `restaurants`
--

DROP TABLE IF EXISTS `restaurants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `restaurants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_id` int NOT NULL,
  `name` varchar(150) NOT NULL,
  `cuisine` varchar(120) DEFAULT NULL,
  `location` varchar(255) NOT NULL,
  `price_tier` varchar(30) DEFAULT NULL,
  `rating` decimal(3,2) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `description` text,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_restaurants_destination_name` (`destination_id`,`name`),
  KEY `ix_restaurants_destination_active` (`destination_id`,`is_active`),
  KEY `ix_restaurants_destination_id` (`destination_id`),
  KEY `ix_restaurants_is_active` (`is_active`),
  CONSTRAINT `restaurants_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `restaurants`
--

LOCK TABLES `restaurants` WRITE;
/*!40000 ALTER TABLE `restaurants` DISABLE KEYS */;
/*!40000 ALTER TABLE `restaurants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `saved_places`
--

DROP TABLE IF EXISTS `saved_places`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `saved_places` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `destination_id` int DEFAULT NULL,
  `hotel_id` int DEFAULT NULL,
  `restaurant_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_saved_places_user_destination` (`user_id`,`destination_id`),
  UNIQUE KEY `uq_saved_places_user_hotel` (`user_id`,`hotel_id`),
  UNIQUE KEY `uq_saved_places_user_restaurant` (`user_id`,`restaurant_id`),
  KEY `ix_saved_places_destination_id` (`destination_id`),
  KEY `ix_saved_places_hotel_id` (`hotel_id`),
  KEY `ix_saved_places_restaurant_id` (`restaurant_id`),
  KEY `ix_saved_places_user_id` (`user_id`),
  CONSTRAINT `saved_places_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `saved_places_ibfk_2` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE,
  CONSTRAINT `saved_places_ibfk_3` FOREIGN KEY (`restaurant_id`) REFERENCES `restaurants` (`id`) ON DELETE CASCADE,
  CONSTRAINT `saved_places_ibfk_4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_saved_places_one_target` CHECK (((((`destination_id` is not null) + (`hotel_id` is not null)) + (`restaurant_id` is not null)) = 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `saved_places`
--

LOCK TABLES `saved_places` WRITE;
/*!40000 ALTER TABLE `saved_places` DISABLE KEYS */;
/*!40000 ALTER TABLE `saved_places` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transport_options`
--

DROP TABLE IF EXISTS `transport_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transport_options` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_id` int DEFAULT NULL,
  `name` varchar(150) NOT NULL,
  `transport_type` varchar(80) DEFAULT NULL,
  `route` varchar(255) NOT NULL,
  `cost_from` decimal(10,2) DEFAULT NULL,
  `duration_text` varchar(120) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transport_options_destination_name_route` (`destination_id`,`name`,`route`),
  KEY `ix_transport_options_destination_active` (`destination_id`,`is_active`),
  KEY `ix_transport_options_destination_id` (`destination_id`),
  KEY `ix_transport_options_is_active` (`is_active`),
  KEY `ix_transport_options_transport_type` (`transport_type`),
  CONSTRAINT `transport_options_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transport_options`
--

LOCK TABLES `transport_options` WRITE;
/*!40000 ALTER TABLE `transport_options` DISABLE KEYS */;
/*!40000 ALTER TABLE `transport_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trip_interests`
--

DROP TABLE IF EXISTS `trip_interests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trip_interests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trip_id` int NOT NULL,
  `interest` varchar(80) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_trip_interests_trip_interest` (`trip_id`,`interest`),
  KEY `ix_trip_interests_trip_id` (`trip_id`),
  CONSTRAINT `trip_interests_ibfk_1` FOREIGN KEY (`trip_id`) REFERENCES `trips` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trip_interests`
--

LOCK TABLES `trip_interests` WRITE;
/*!40000 ALTER TABLE `trip_interests` DISABLE KEYS */;
/*!40000 ALTER TABLE `trip_interests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trips`
--

DROP TABLE IF EXISTS `trips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trips` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `destination_id` int NOT NULL,
  `start_date` date NOT NULL,
  `number_of_days` int NOT NULL,
  `travelers` int NOT NULL,
  `budget` varchar(80) DEFAULT NULL,
  `transport_preference` varchar(80) DEFAULT NULL,
  `accommodation_preference` varchar(80) DEFAULT NULL,
  `status` varchar(30) NOT NULL,
  `share_id` varchar(32) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_trips_share_id` (`share_id`),
  KEY `ix_trips_destination_id` (`destination_id`),
  KEY `ix_trips_status` (`status`),
  KEY `ix_trips_user_destination_start` (`user_id`,`destination_id`,`start_date`),
  KEY `ix_trips_user_id` (`user_id`),
  CONSTRAINT `trips_ibfk_1` FOREIGN KEY (`destination_id`) REFERENCES `destinations` (`id`),
  CONSTRAINT `trips_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trips`
--

LOCK TABLES `trips` WRITE;
/*!40000 ALTER TABLE `trips` DISABLE KEYS */;
/*!40000 ALTER TABLE `trips` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(30) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_role` (`role`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (7,'Manas Diwan','manas@gmail.com','scrypt:32768:8:1$nDCtwzuWi36WYYGt$f9781d32dcf7315fae8a9fe1e1cc39f29fc06464e1fad1c40c7c1becc03a443d8e4b4d2e17e9b927a16c608eb90735ca881755845f3a8bf08e4c3a6fd156ceb3','tourist',1,'2026-08-19 13:38:43','2026-08-19 13:38:43'),(8,'first test','test@gmail.com','scrypt:32768:8:1$WWUOJ53rdvcpM5yH$9298ff017971388747f1996c184c453dc2147ed0a4031dc2cd9c8958fe1e021de8ef87774fd51cf16b8b5320bb93332fcf2bfacca8f5c1818b867cfd28f95b41','tourist',1,'2026-08-21 05:53:42','2026-08-21 05:53:42'),(9,'Yash Vinod','yash123@gmail.com','scrypt:32768:8:1$9xVQA7reRMUWypy4$bd481278b3bf1e40b617e198c59442ca71e6b4f2feb296baa848ad67400cc0046e4190f8d4c757140543030ae39db3a90d012c7fcfdf11665e92017e3f501a3c','tourist',1,'2026-08-21 05:59:28','2026-08-21 05:59:28'),(10,'vinay krishan','vinayrithika@gmail.com','scrypt:32768:8:1$J6grYOm3DkClllF0$6006ab7919bd10e057ecd0b6d684c6d1ea31a3a6d40654731e24727b87254d5c58910d7bd35f76fb34d5e08a6e4da7200a0dd2d02c7920c2d3ea8dd194dcfcc9','tourist',1,'2026-08-21 06:02:16','2026-08-21 06:02:16'),(11,'test2','test2@gmail.com','scrypt:32768:8:1$YEKKI0VDktb5XukY$76546b7f1cc761f14b5b5c12c8786bb4d1f582746f847bdece1050263ee8a0ea59ae12816d8b9ff50e166671e0a0ed4fe4a203222475b95caf0c677b34baabb9','tourist',1,'2026-08-24 04:48:03','2026-08-24 04:48:03'),(12,'Integration Tourist','integration-7ae294108438@example.test','scrypt:32768:8:1$M1vEHEioZwLV9niv$197dfd74f1aaaa98006965e1e8d04235c20eb6ecd748292a7c2f47969a2356241f20792b299d9ed91b503249429c2ded463b57fccb0b6564fa054d2baf414d17','tourist',1,'2026-08-24 05:09:23','2026-08-24 05:09:23'),(13,'Integration Tourist','integration-3cb812526214@example.test','scrypt:32768:8:1$tzLFCngOwd6Hr0zT$dfabf74f7fbcc8fa8d37f6e1e71257d70efc12476182177060eaf95bf2eda498a4067aa89406ef1b0159f2402cfbeca449452537dbae62b95b2d8a8eafdbfae4','tourist',1,'2026-08-24 05:09:34','2026-08-24 05:09:34'),(14,'Tourisense Government','admin@gmail.com','scrypt:32768:8:1$js4NIsU6LudOi37x$d5a3a9ae897a58ee5ab868409f74a2d2390b5118b461377d054c3f822e2bf2940a1a9cf12e6bc094c2cb23390b94d1cf5230a0bf271c35eb4c45264f7645b62b','admin',1,'2026-08-24 05:18:46','2026-08-24 05:18:46'),(15,'test3','test3@gmail.com','scrypt:32768:8:1$qMa5veHg8FHKZWPQ$c06cf17be5ca87af419192711aa24004fd71c608e55aadc74ed8a21d8f4151bfe9be7baf231f4e13cba8987485f59f4980cd1e4bcc92e2c28aed2c6c5bf0ff59','tourist',1,'2026-08-24 05:22:08','2026-08-24 05:22:08'),(16,'test4','test4@gmail.com','scrypt:32768:8:1$UibuJ6LsY0PwsZow$a1a1f3fd4daa2bc5786762c744aa24ec595a86943c971523a805b2e05c0f8b3ddeefe01aa82379f03268316e9df34a46a184b1ce65ab660d4d7157e756444e6a','tourist',1,'2026-08-25 05:57:02','2026-08-25 05:57:02'),(17,'likitha','likitha@gmail.com','scrypt:32768:8:1$rSaH7Lj3Tc2jLrfD$18019265eb957fff48837d797efe80cb4673e6c2a368d49e9bbc7c02f42147e7f971372c2717041cc196e5f382dd4ecc879e07641ecc385437572317b041b8f2','tourist',1,'2026-08-25 06:21:34','2026-08-25 06:21:34');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-26 18:58:14
