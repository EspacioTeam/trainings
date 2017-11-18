-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema ctf
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema ctf
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ctf` DEFAULT CHARACTER SET utf8 ;
USE `ctf` ;

-- -----------------------------------------------------
-- Table `ctf`.`user`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ctf`.`user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `token` VARCHAR(128) NOT NULL,
  `name` VARCHAR(45) NULL,
  `score` INT NOT NULL DEFAULT 0,
  `regdate` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `host` varchar(40) NULL DEFAULT '127.0.0.1',
  `status` TINYINT NULL DEFAULT 104,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `token_UNIQUE` (`token` ASC),
  UNIQUE INDEX `name_UNIQUE`  (`name` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `ctf`.`flag`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ctf`.`flag` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `flag` VARCHAR(256) NOT NULL,
  `points` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `flag_UNIQUE` (`flag` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `ctf`.`submissions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ctf`.`submissions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `date` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `flag_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_submissions_user_idx` (`user_id` ASC),
  INDEX `fk_submissions_flag1_idx` (`flag_id` ASC),
  CONSTRAINT `fk_submissions_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ctf`.`user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_submissions_flag1`
    FOREIGN KEY (`flag_id`)
    REFERENCES `ctf`.`flag` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
