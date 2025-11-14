CREATE TABLE "provinces" (
  "province_id" uuid PRIMARY KEY,
  "name" varchar(255),
  "name_dari" varchar(255),
  "name_pashto" varchar(255),
  "code" varchar(10) UNIQUE,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "districts" (
  "district_id" uuid PRIMARY KEY,
  "province_id" uuid NOT NULL,
  "name" varchar(255),
  "name_dari" varchar(255),
  "name_pashto" varchar(255),
  "code" varchar(10),
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "clinics" (
  "clinic_id" uuid PRIMARY KEY,
  "district_id" uuid NOT NULL,
  "name" varchar(255),
  "clinic_code" varchar(50) UNIQUE,
  "address" text,
  "supervisor_id" uuid,
  "latitude" decimal(10,8),
  "longitude" decimal(11,8),
  "is_active" boolean,
  "capacity" integer,
  "equipment_available" jsonb,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "users" (
  "user_id" uuid PRIMARY KEY,
  "username" varchar(100) UNIQUE NOT NULL,
  "email" varchar(255),
  "full_name" varchar(255),
  "role" varchar(50),
  "clinic_id" uuid,
  "language_preference" varchar(10),
  "phone" varchar(20),
  "is_active" boolean,
  "last_login" timestamptz,
  "password_hash" varchar(255),
  "created_by" uuid,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "children" (
  "child_id" uuid PRIMARY KEY,
  "first_name" varchar(255),
  "father_name" varchar(255),
  "date_of_birth" date,
  "sex" varchar(10),
  "clinic_id" uuid,
  "caregiver_name" varchar(255),
  "caregiver_phone" varchar(20),
  "caregiver_whatsapp" varchar(20),
  "caregiver_relationship" varchar(50),
  "village_address" text,
  "enrollment_date" date,
  "enrolled_by" uuid,
  "is_active" boolean,
  "discharge_date" date,
  "discharge_reason" text,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "consent_records" (
  "consent_id" uuid PRIMARY KEY,
  "child_id" uuid NOT NULL,
  "health_worker_id" uuid NOT NULL,
  "photo_consent" boolean,
  "data_storage_consent" boolean,
  "data_sharing_consent" boolean,
  "whatsapp_consent" boolean,
  "consent_method" varchar(50),
  "witness_name" varchar(255),
  "consent_date" timestamptz,
  "consent_expires_at" timestamptz,
  "notes" text,
  "created_at" timestamptz
);

CREATE TABLE "consent_artifacts" (
  "artifact_id" uuid PRIMARY KEY,
  "consent_id" uuid NOT NULL,
  "artifact_type" varchar(40),
  "storage_path" varchar(500) NOT NULL,
  "content_type" varchar(50),
  "file_size_bytes" bigint,
  "checksum" text,
  "captured_by" uuid,
  "captured_at" timestamptz
);

CREATE TABLE "cases" (
  "case_id" uuid PRIMARY KEY,
  "child_id" uuid NOT NULL,
  "clinic_id" uuid,
  "start_date" date NOT NULL,
  "end_date" date,
  "status" varchar(20),
  "discharge_reason" text,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "assessments" (
  "assessment_id" uuid PRIMARY KEY,
  "child_id" uuid NOT NULL,
  "health_worker_id" uuid NOT NULL,
  "clinic_id" uuid,
  "case_id" uuid,
  "assessment_date" date,
  "assessment_time" time,
  "age_months" integer,
  "weight_kg" decimal(5,2),
  "height_cm" decimal(5,2),
  "measurement_type" varchar(20),
  "manual_muac_cm" decimal(4,2),
  "wfh_zscore" decimal(5,2),
  "wfa_zscore" decimal(5,2),
  "hfa_zscore" decimal(5,2),
  "ai_muac_cm" decimal(4,2),
  "ai_muac_confidence" decimal(5,4),
  "ai_muac_processing_status" varchar(50),
  "ai_edema_detected" boolean,
  "ai_edema_confidence" decimal(5,4),
  "ai_edema_processing_status" varchar(50),
  "ai_hair_changes_detected" boolean,
  "ai_hair_confidence" decimal(5,4),
  "ai_skin_analysis" jsonb,
  "ai_processing_status" varchar(50),
  "ai_error_message" text,
  "ai_processed_at" timestamptz,
  "edema_physical_test" boolean,
  "edema_location" varchar(100),
  "has_low_appetite" boolean,
  "is_lethargic" boolean,
  "has_dehydration" boolean,
  "has_temperature_risk" boolean,
  "has_rapid_breathing" boolean,
  "has_skin_infections" boolean,
  "has_diarrhea" boolean,
  "has_vomiting" boolean,
  "has_diarrhea_or_vomiting" boolean,
  "dehydration_status" varchar(50),
  "has_fever" boolean,
  "temperature_celsius" decimal(4,2),
  "respiratory_rate" integer,
  "has_severe_illness" boolean,
  "danger_signs_notes" text,
  "nutrition_status" varchar(50),
  "sam_type" varchar(50),
  "has_stunting" boolean,
  "has_wasting" boolean,
  "treatment_recommendation" text,
  "next_followup_date" date,
  "assessment_duration_seconds" integer,
  "sync_status" varchar(50),
  "synced_at" timestamptz,
  "notes" text,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "assessment_media" (
  "media_id" uuid PRIMARY KEY,
  "assessment_id" uuid NOT NULL,
  "media_type" varchar(20),
  "content_type" varchar(50),
  "storage_path" varchar(500),
  "file_size_bytes" bigint,
  "mime_type" varchar(50),
  "reference_object_type" varchar(50),
  "reference_object_size_mm" decimal(6,2),
  "quality_score" decimal(3,2),
  "quality_status" varchar(50),
  "quality_issues" jsonb,
  "uploaded_at" timestamptz,
  "processed" boolean,
  "processed_at" timestamptz,
  "camera_metadata" jsonb
);

CREATE TABLE "followups" (
  "followup_id" uuid PRIMARY KEY,
  "child_id" uuid NOT NULL,
  "assessment_id" uuid,
  "case_id" uuid,
  "scheduled_date" date,
  "scheduled_by" uuid,
  "followup_type" varchar(50),
  "completed_date" date,
  "completed_by" uuid,
  "missed" boolean,
  "missed_reason" varchar(255),
  "missed_attempts" integer,
  "rescheduled_date" date,
  "reminder_sent" boolean,
  "reminder_sent_at" timestamptz,
  "reminder_method" varchar(50),
  "notes" text,
  "created_at" timestamptz,
  "updated_at" timestamptz
);

CREATE TABLE "assessment_reviews" (
  "review_id" uuid PRIMARY KEY,
  "assessment_id" uuid NOT NULL,
  "reviewer_id" uuid NOT NULL,
  "status" varchar(20),
  "notes" text,
  "created_at" timestamptz
);

CREATE TABLE "referrals" (
  "referral_id" uuid PRIMARY KEY,
  "assessment_id" uuid NOT NULL,
  "issued_by" uuid,
  "approved_by" uuid,
  "destination_facility" varchar(255),
  "urgency" varchar(20),
  "reason" text,
  "status" varchar(20),
  "issued_at" timestamptz,
  "arrived_at" timestamptz,
  "completed_at" timestamptz
);

CREATE TABLE "training_images" (
  "training_image_id" uuid PRIMARY KEY,
  "image_type" varchar(50),
  "storage_path" varchar(500),
  "file_size_bytes" bigint,
  "ground_truth_muac_cm" decimal(4,2),
  "ground_truth_edema" boolean,
  "ground_truth_hair_changes" boolean,
  "ground_truth_skin_condition" varchar(100),
  "reference_object_type" varchar(50),
  "reference_object_size_mm" decimal(6,2),
  "image_quality_score" decimal(3,2),
  "validated" boolean,
  "validated_by" uuid,
  "validated_at" timestamptz,
  "validation_notes" text,
  "metadata" jsonb,
  "used_in_training" boolean,
  "training_batch_id" varchar(100),
  "created_at" timestamptz
);

CREATE TABLE "audit_log" (
  "log_id" uuid PRIMARY KEY,
  "user_id" uuid,
  "action" varchar(100),
  "entity_type" varchar(50),
  "entity_id" uuid,
  "old_values" jsonb,
  "new_values" jsonb,
  "ip_address" inet,
  "user_agent" text,
  "device_info" jsonb,
  "timestamp" timestamptz
);

CREATE TABLE "sync_queue" (
  "queue_id" uuid PRIMARY KEY,
  "user_id" uuid,
  "entity_type" varchar(50),
  "entity_id" uuid,
  "operation" varchar(20),
  "payload" jsonb,
  "sync_status" varchar(50),
  "attempts" integer,
  "last_attempt_at" timestamptz,
  "error_message" text,
  "priority" integer,
  "created_at" timestamptz,
  "synced_at" timestamptz
);

ALTER TABLE "districts" ADD FOREIGN KEY ("province_id") REFERENCES "provinces" ("province_id");

ALTER TABLE "clinics" ADD FOREIGN KEY ("district_id") REFERENCES "districts" ("district_id");

ALTER TABLE "clinics" ADD FOREIGN KEY ("supervisor_id") REFERENCES "users" ("user_id");

ALTER TABLE "users" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("clinic_id");

ALTER TABLE "users" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("user_id");

ALTER TABLE "children" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("clinic_id");

ALTER TABLE "children" ADD FOREIGN KEY ("enrolled_by") REFERENCES "users" ("user_id");

ALTER TABLE "consent_records" ADD FOREIGN KEY ("child_id") REFERENCES "children" ("child_id");

ALTER TABLE "consent_records" ADD FOREIGN KEY ("health_worker_id") REFERENCES "users" ("user_id");

ALTER TABLE "consent_artifacts" ADD FOREIGN KEY ("consent_id") REFERENCES "consent_records" ("consent_id");

ALTER TABLE "consent_artifacts" ADD FOREIGN KEY ("captured_by") REFERENCES "users" ("user_id");

ALTER TABLE "cases" ADD FOREIGN KEY ("child_id") REFERENCES "children" ("child_id");

ALTER TABLE "cases" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("clinic_id");

ALTER TABLE "assessments" ADD FOREIGN KEY ("child_id") REFERENCES "children" ("child_id");

ALTER TABLE "assessments" ADD FOREIGN KEY ("health_worker_id") REFERENCES "users" ("user_id");

ALTER TABLE "assessments" ADD FOREIGN KEY ("clinic_id") REFERENCES "clinics" ("clinic_id");

ALTER TABLE "assessments" ADD FOREIGN KEY ("case_id") REFERENCES "cases" ("case_id");

ALTER TABLE "assessment_media" ADD FOREIGN KEY ("assessment_id") REFERENCES "assessments" ("assessment_id");

ALTER TABLE "followups" ADD FOREIGN KEY ("child_id") REFERENCES "children" ("child_id");

ALTER TABLE "followups" ADD FOREIGN KEY ("assessment_id") REFERENCES "assessments" ("assessment_id");

ALTER TABLE "followups" ADD FOREIGN KEY ("scheduled_by") REFERENCES "users" ("user_id");

ALTER TABLE "followups" ADD FOREIGN KEY ("completed_by") REFERENCES "users" ("user_id");

ALTER TABLE "followups" ADD FOREIGN KEY ("case_id") REFERENCES "cases" ("case_id");

ALTER TABLE "assessment_reviews" ADD FOREIGN KEY ("assessment_id") REFERENCES "assessments" ("assessment_id");

ALTER TABLE "assessment_reviews" ADD FOREIGN KEY ("reviewer_id") REFERENCES "users" ("user_id");

ALTER TABLE "referrals" ADD FOREIGN KEY ("assessment_id") REFERENCES "assessments" ("assessment_id");

ALTER TABLE "referrals" ADD FOREIGN KEY ("issued_by") REFERENCES "users" ("user_id");

ALTER TABLE "referrals" ADD FOREIGN KEY ("approved_by") REFERENCES "users" ("user_id");

ALTER TABLE "training_images" ADD FOREIGN KEY ("validated_by") REFERENCES "users" ("user_id");

ALTER TABLE "audit_log" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");

ALTER TABLE "sync_queue" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
