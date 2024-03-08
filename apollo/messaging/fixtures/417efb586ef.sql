INSERT INTO public.deployment (id, name, hostnames, allow_observer_submission_edit, include_rejected_in_votes, is_initialized, dashboard_full_locations, uuid, primary_locale, other_locales, enable_partial_response_for_messages, brand_image) VALUES (1, 'Default', '{localhost}', true, false, false, true, 'd3f90a73-0268-4191-9d8f-55fdc7f54c50', NULL, NULL, NULL, NULL);
INSERT INTO public.location_set (id, name, slug, deployment_id, uuid, is_finalized) VALUES (1, 'Test Location set', NULL, 1, 'f1c1baf2-c00b-4903-ba60-1e113a1ffd8b', true);
INSERT INTO public.location_type (id, is_administrative, is_political, has_registered_voters, slug, location_set_id, uuid, name_translations, has_coordinates) VALUES 
    (1, false, false, false, NULL, 1, 'e6943645-df51-4f9e-af20-89c1963f1fbc', '{"en": "Root"}', false),
    (2, false, false, false, NULL, 1, '6a6730f6-2474-4e20-b896-3a8eb41451a3', '{"en": "Trunk"}', false),
    (3, false, false, false, NULL, 1, '15f18556-d55d-4d9e-a2db-5d5ea275601c', '{"en": "Branch"}', false),
    (4, false, false, false, NULL, 1, '38cabd15-1e9d-4247-8571-59e362f6a0f4', '{"en": "Leaf"}', false);
INSERT INTO public.participant_set (id, name, slug, location_set_id, deployment_id, uuid, gender_hidden, partner_hidden, role_hidden) VALUES
    (1, 'Test Participant set', NULL, 1, 1, '59f937c7-e024-4746-b2d3-fa46e2f16918', false, false, false),
    (2, 'Other test participant set', NULL, 1, 1, 'e1902474-b22c-401c-80c5-4e94c396c793', false, false, false);
INSERT INTO public.participant (id, participant_id, role_id, partner_id, supervisor_id, gender, email, location_id, participant_set_id, message_count, accurate_message_count, completion_rating, device_id, password, extra_data, uuid, full_name_translations, first_name_translations, last_name_translations, other_names_translations, locale) VALUES
    (1, '403794', NULL, NULL, NULL, 'F', NULL, NULL, 1, 0, 0, 1, NULL, 'UWenJK', NULL, 'c3cf0d83-1b40-4569-85c6-00dfe4070c10', '{}', '{"en": "Prudence"}', '{"en": "Moreinu"}', '{}', NULL),
    (2, '269156', NULL, NULL, NULL, 'M', NULL, NULL, 1, 0, 0, 1, NULL, 'fEP3hb', NULL, 'c2bcec62-bc61-4856-abc9-01aa77a59f13', '{}', '{"en": "Allyn"}', '{"en": "Cridland"}', '{}', NULL),
    (3, '221498', NULL, NULL, NULL, 'F', NULL, NULL, 1, 0, 0, 1, NULL, 'EDGINw', NULL, '6d506c74-9237-48fe-8b2a-51851db63797', '{}', '{"en": "Gerhardine"}', '{"en": "Enrich"}', '{}', NULL),
    (4, '966943', NULL, NULL, NULL, 'F', NULL, NULL, 1, 0, 0, 1, NULL, 'u1HeyF', NULL, '742cd245-9e1a-4237-8270-a910d5c1586f', '{}', '{"en": "Tamarah"}', '{"en": "Cape"}', '{}', NULL),
    (5, '902318', NULL, NULL, NULL, 'F', NULL, NULL, 1, 0, 0, 1, NULL, 'HFNKid', NULL, 'e74b8893-98da-438c-bd22-beb379b6579f', '{}', '{"en": "Shannon"}', '{"en": "Fernihough"}', '{}', NULL),
    (6, '403794', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, 'XbcslG', NULL, '1f8b1a2e-9356-43cd-9550-457f52185d41', '{}', '{"en": "Prudence"}', '{"en": "Moreinu"}', '{}', NULL),
    (7, '269156', NULL, NULL, NULL, 'M', NULL, NULL, 2, 0, 0, 1, NULL, 'nbLeVe', NULL, 'a70c6fdf-f3c4-4916-86f6-8de43cacb850', '{}', '{"en": "Allyn"}', '{"en": "Cridland"}', '{}', NULL),
    (8, '221498', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, 'c5eIRC', NULL, 'c59d9684-fe8f-4186-9c6b-cfb3e9ee5724', '{}', '{"en": "Gerhardine"}', '{"en": "Enrich"}', '{}', NULL),
    (9, '966943', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, 'NfjV7N', NULL, '80928dcc-ce49-445b-b3ea-c0d806fbe018', '{}', '{"en": "Tamarah"}', '{"en": "Cape"}', '{}', NULL),
    (10, '902318', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, '6z2mWE', NULL, 'e73fbf73-8590-4c38-b322-79308071db75', '{}', '{"en": "Shannon"}', '{"en": "Fernihough"}', '{}', NULL),
    (11, '308158', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, 'tzdqRl', NULL, '967da4b8-e4fd-43f4-9ae3-178b3c7a554d', '{}', '{"en": "Vanna"}', '{"en": "Waller"}', '{}', NULL),
    (12, '188339', NULL, NULL, NULL, 'F', NULL, NULL, 2, 0, 0, 1, NULL, 'gTMGQE', NULL, 'a2c497cc-b654-4368-97fa-b353a12883b8', '{}', '{"en": "Dorelle"}', '{"en": "Tempest"}', '{}', NULL),
    (13, '837994', NULL, NULL, NULL, 'M', NULL, NULL, 2, 0, 0, 1, NULL, 'Vl095i', NULL, '9bfe9102-0907-40c1-8180-c8975a93b831', '{}', '{"en": "Dudley"}', '{"en": "Russe"}', '{}', NULL),
    (14, '534165', NULL, NULL, NULL, '', NULL, NULL, 2, 0, 0, 1, NULL, 'Ha54MJ', NULL, 'ea0860a7-8ad7-4b75-a8b1-4daa719afd86', '{}', '{"en": "Bobbe"}', '{"en": "Loker"}', '{}', NULL),
    (15, '889412', NULL, NULL, NULL, 'M', NULL, NULL, 2, 0, 0, 1, NULL, 'CItcDB', NULL, 'b118e250-1fa1-493d-939a-e4d677722b25', '{}', '{"en": "Obadiah"}', '{"en": "Fery"}', '{}', NULL);
INSERT INTO public.resource (resource_id, resource_type, deployment_id, uuid) VALUES
    (1, 'event', 1, 'b6739da2-ccce-40c4-858b-4e358f210728'),
    (2, 'event', 1, '32168dea-21b0-41d0-a3fb-409424fb4c7d');
INSERT INTO public.resource (resource_id, resource_type, deployment_id, uuid) VALUES (3, 'event', 1, '151904d4-8c6a-422d-86c2-187dcfbe9143');
INSERT INTO public.event (id, name, start, "end", resource_id, location_set_id, participant_set_id) VALUES
    (1, 'Default', '1970-01-01 01:00:00+01', '1970-01-01 01:00:00+01', 1, NULL, NULL),
    (2, 'Event 1', '2024-03-06 00:00:00+01', '2024-03-06 23:59:59+01', 2, 1, 1);
INSERT INTO public.event (id, name, start, "end", resource_id, location_set_id, participant_set_id) VALUES (3, 'Event 2', '2024-03-06 00:00:00+01', '2024-03-06 23:59:59+01', 3, 1, 2);
INSERT INTO public.location_type_path (location_set_id, ancestor_id, descendant_id, depth) VALUES
    (1, 1, 1, 0),
    (1, 1, 2, 1),
    (1, 1, 3, 2),
    (1, 1, 4, 3),
    (1, 2, 2, 0),
    (1, 2, 3, 1),
    (1, 2, 4, 2),
    (1, 3, 3, 0),
    (1, 3, 4, 1),
    (1, 4, 4, 0);
INSERT INTO public.phone_contact (id, participant_id, number, created, updated, verified, uuid) VALUES
    (1, 1, '7477150532', '2024-03-06 19:03:41.001538', '2024-03-06 19:03:41.001564', true, '0a3980d6-c590-4e55-8f86-34589c6cae61'),
    (2, 2, '7326767526', '2024-03-06 19:03:41.038186', '2024-03-06 19:03:41.0382', true, '51645dad-700d-4d40-a929-f93a662335b4'),
    (3, 3, '7918535792', '2024-03-06 19:03:41.069597', '2024-03-06 19:03:41.069626', true, '4db683aa-766b-42b6-b584-5e95500a9759'),
    (4, 4, '1634556353', '2024-03-06 19:03:41.100529', '2024-03-06 19:03:41.100546', true, '720e875a-5766-4bd6-8f02-7cc26e23e078'),
    (5, 5, '8075223410', '2024-03-06 19:03:41.125142', '2024-03-06 19:03:41.125156', true, '595e3c05-10fa-436f-9ef2-6378975b5b1b'),
    (6, 6, '7477150532', '2024-03-06 19:08:58.85081', '2024-03-06 19:08:58.850825', true, 'c0169a36-e54d-4685-8624-bd5d2479e080'),
    (7, 7, '7326767526', '2024-03-06 19:08:58.892082', '2024-03-06 19:08:58.892095', true, 'd8788abb-1d8e-411e-8afb-32e3523e820d'),
    (8, 8, '7918535792', '2024-03-06 19:08:58.928059', '2024-03-06 19:08:58.928076', true, '6f4eded8-7e0e-4e30-9879-c85571f26b78'),
    (9, 9, '1634556353', '2024-03-06 19:08:58.956878', '2024-03-06 19:08:58.956894', true, '88da7909-57c4-4269-88b4-41624e178968'),
    (10, 10, '8075223410', '2024-03-06 19:08:58.985415', '2024-03-06 19:08:58.985429', true, '08afc7da-5eab-466f-8738-effbabdfe5a1'),
    (11, 11, '5906502001', '2024-03-06 19:09:26.510655', '2024-03-06 19:09:26.510669', true, 'def0a41f-9a15-4398-a5cb-39725816b5b8'),
    (12, 12, '9212669395', '2024-03-06 19:09:26.550223', '2024-03-06 19:09:26.550247', true, '43f6d993-7e8f-4a71-ae7c-e8b77627e0bb'),
    (13, 13, '1398768677', '2024-03-06 19:09:26.578216', '2024-03-06 19:09:26.578231', true, '57bb4f5a-2175-4860-88c3-244d08369a08'),
    (14, 14, '9791825394', '2024-03-06 19:09:26.609561', '2024-03-06 19:09:26.609577', true, '42fe3197-47cf-4c42-943f-95c71dd2c159'),
    (15, 15, '2823234079', '2024-03-06 19:09:26.637955', '2024-03-06 19:09:26.637972', true, '6f0d7457-9d90-4518-b04b-ad25759234e2');
SELECT pg_catalog.setval('public.contact_history_id_seq', 1, false);
SELECT pg_catalog.setval('public.deployment_id_seq', 1, true);
SELECT pg_catalog.setval('public.event_id_seq', 3, true);
SELECT pg_catalog.setval('public.form_id_seq', 1, false);
SELECT pg_catalog.setval('public.image_attachment_id_seq', 1, false);
SELECT pg_catalog.setval('public.location_data_field_id_seq', 1, false);
SELECT pg_catalog.setval('public.location_group_id_seq', 1, false);
SELECT pg_catalog.setval('public.location_id_seq', 1, false);
SELECT pg_catalog.setval('public.location_set_id_seq', 1, true);
SELECT pg_catalog.setval('public.location_type_id_seq', 4, true);
SELECT pg_catalog.setval('public.message_id_seq', 1, false);
SELECT pg_catalog.setval('public.participant_data_field_id_seq', 1, false);
SELECT pg_catalog.setval('public.participant_id_seq', 15, true);
SELECT pg_catalog.setval('public.participant_partner_id_seq', 1, false);
SELECT pg_catalog.setval('public.participant_role_id_seq', 2, true);
SELECT pg_catalog.setval('public.participant_set_id_seq', 2, true);
SELECT pg_catalog.setval('public.phone_contact_id_seq', 15, true);
SELECT pg_catalog.setval('public.resource_resource_id_seq', 3, true);
