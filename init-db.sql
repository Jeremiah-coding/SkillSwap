-- Create service databases
CREATE DATABASE identity_profiles_db;
CREATE DATABASE sessions_db;
CREATE DATABASE notifications_db;

-- Grant privileges to skillswap user
GRANT ALL PRIVILEGES ON DATABASE identity_profiles_db TO skillswap;
GRANT ALL PRIVILEGES ON DATABASE sessions_db TO skillswap;
GRANT ALL PRIVILEGES ON DATABASE notifications_db TO skillswap;
