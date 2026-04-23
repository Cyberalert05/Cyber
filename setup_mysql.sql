CREATE DATABASE IF NOT EXISTS `tweet_monitoring`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `tweet_monitoring`;

CREATE TABLE IF NOT EXISTS `tweets` (
  `id_tweet` varchar(255) NOT NULL,
  `dt_object` datetime DEFAULT NULL,
  `tweet_created` varchar(255) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  `profile_picture` text,
  `tweet_type` varchar(50) DEFAULT NULL,
  `tweet_text` text,
  `media_url` text,
  `location` varchar(255) DEFAULT NULL,
  `latitude` varchar(50) DEFAULT NULL,
  `longitude` varchar(50) DEFAULT NULL,
  `text_toxicity` text DEFAULT NULL,
  `image_class` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_tweet`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `hashtags` (
  `tag` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

