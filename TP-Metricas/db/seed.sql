-- =============================================================================
-- Seed: test users
-- Passwords are bcrypt hashes of the value shown in the comment.
-- Generate new hashes with: python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('PASSWORD'))"
-- =============================================================================

INSERT INTO users (username, password_hash, email, full_name) VALUES
-- password: admin123
('admin',     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4oUHaJ5FUi', 'admin@ticketsystem.com',    'Administrador'),
-- password: test123
('test_user', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'testuser@example.com',      'Usuario de Prueba'),
('testuser1', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user1@example.com',         'Usuario de Prueba 1'),
('testuser2', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user2@example.com',         'Usuario de Prueba 2'),
('testuser3', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user3@example.com',         'Usuario de Prueba 3'),
('testuser4', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user4@example.com',         'Usuario de Prueba 4'),
('testuser5', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user5@example.com',         'Usuario de Prueba 5'),
('testuser6', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user6@example.com',         'Usuario de Prueba 6'),
('testuser7', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user7@example.com',         'Usuario de Prueba 7'),
('testuser8', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user8@example.com',         'Usuario de Prueba 8'),
('testuser9', '$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user9@example.com',         'Usuario de Prueba 9'),
('testuser10','$2b$12$8K1p/a0dR1xWRIgF.nUwse.K3F5Y4L/XxHK8Q1a2ZdP3vMOK7fVSq', 'user10@example.com',        'Usuario de Prueba 10'),
-- password: kevin123
('kevin',     '$2b$12$vvVbPxpuoVbJF.cMmGHrBOhQHhVe3U6Xu6e.2JqmVRxGOJz4ZiHqe', 'kevin@example.com',         'Kevin Arias')
ON CONFLICT (username) DO NOTHING;
