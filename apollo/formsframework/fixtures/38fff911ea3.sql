INSERT INTO public.deployment VALUES (1, 'Demo', '{localhost}', true, NULL, false, false, true, NULL, NULL, 'cedd906b-b461-4ea9-9b7c-ac169badda08');
INSERT INTO public.resource VALUES (1, 'event', 1, '7273bdfa-07d5-4642-9e0f-e2e72b5bfc74');
INSERT INTO public.resource VALUES (2, 'event', 1, 'afbd2aef-fcc2-4336-a9b2-01ae5ac9ed4c');
INSERT INTO public.resource VALUES (3, 'event', 1, '538ee2bd-331f-4041-a0eb-5b456b517141');
INSERT INTO public.resource VALUES (4, 'form', 1, 'bec1f1cc-a4d8-4798-b763-e17b6ba5d128');
INSERT INTO public.resource VALUES (5, 'form', 1, '1c6547b0-e21c-4f13-8ea8-802d725d6559');
INSERT INTO public.resource VALUES (6, 'form', 1, 'a0efcdf3-8f09-4d15-8303-6c720bbf7536');
INSERT INTO public.resource VALUES (7, 'form', 1, '1a8b8e90-ac70-435e-8dfa-0f5ecec33246');
INSERT INTO public.resource VALUES (8, 'form', 1, '28de096e-3ea9-48f9-8b24-12ba6142c202');
INSERT INTO public.resource VALUES (9, 'form', 1, '2856962f-d9d0-4ad5-bf99-1a40d86db1fa');
INSERT INTO public.event VALUES (1, 'Event 1', '2005-12-13 01:00:00+01', '2005-12-14 00:59:59+01', 1,NULL, NULL);
INSERT INTO public.event VALUES (2, 'Event 2', '2005-12-14 01:00:00+01', '2005-12-15 00:59:59+01', 2,NULL, NULL);
INSERT INTO public.event VALUES (3, 'Event 3', '2005-12-14 01:00:00+01', '2005-12-16 00:59:59+01', 3,NULL, NULL);
INSERT INTO public.form VALUES (1, 'CH-1-1', 'XA', 'CHECKLIST', true, true, NULL, '8f389707f29d43af9a423b93a9b1bb7c', 4, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
INSERT INTO public.form VALUES (2, 'IN-1-1', 'XB', 'INCIDENT', true, true, NULL, '7d9f6f02091e45c5a3567235e940bf20', 5, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
INSERT INTO public.form VALUES (3, 'IN-2-1', 'ZA', 'INCIDENT', true, true, NULL, '5e50b822cbf94fedb76619f1808716b2', 6, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
INSERT INTO public.form VALUES (4, 'CH-3-1', 'WA', 'CHECKLIST', true, true, NULL, 'aac237a0844d414e8635ed054ab27333', 7, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
INSERT INTO public.form VALUES (5, 'CH-3-2', 'WB', 'CHECKLIST', true, true, NULL, '64f973d56a55469da34ea3ec6b7ae2c8', 8, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
INSERT INTO public.form VALUES (6, 'IN-3-1', 'WC', 'INCIDENT', true, true, NULL, '34d79b36acf74dd99bbf8b68631f587c', 9, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL);
SELECT pg_catalog.setval('public.deployment_id_seq', 1, true);
SELECT pg_catalog.setval('public.event_id_seq', 3, true);
SELECT pg_catalog.setval('public.form_id_seq', 6, true);
SELECT pg_catalog.setval('public.resource_resource_id_seq', 9, true);
