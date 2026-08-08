-- Dev seed: one business, one service, two counters, one open queue for today.
-- Two counters matter: they make the call-next race real to test against.
-- Fixed UUIDs so curl commands stay copy-paste stable across re-seeds.

DELETE FROM queue_events;
DELETE FROM queue_entries;
DELETE FROM queues;
DELETE FROM counters;
DELETE FROM services;
DELETE FROM businesses;

INSERT INTO businesses (id, name, email) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Test Clinic', 'owner@testclinic.dev');

INSERT INTO services (id, name, business_id) VALUES
    ('22222222-2222-2222-2222-222222222222', 'General Checkup', '11111111-1111-1111-1111-111111111111');

INSERT INTO counters (id, label, is_active, service_id) VALUES
    ('33333333-3333-3333-3333-333333333333', 'Counter A', true, '22222222-2222-2222-2222-222222222222'),
    ('44444444-4444-4444-4444-444444444444', 'Counter B', true, '22222222-2222-2222-2222-222222222222');

INSERT INTO queues (id, date, status, next_position, service_id) VALUES
    ('55555555-5555-5555-5555-555555555555', CURRENT_DATE, 'open', 0, '22222222-2222-2222-2222-222222222222');
