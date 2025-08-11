# Migration Guide: SQLite to PostgreSQL

## Quick Migration Steps:

### 1. Install PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Create database and user
createdb rescuetime
psql rescuetime -c "CREATE USER rescuetime_user WITH PASSWORD 'your_password';"
psql rescuetime -c "GRANT ALL PRIVILEGES ON DATABASE rescuetime TO rescuetime_user;"
```

### 2. Install Python Dependencies
```bash
pip install psycopg2-binary
```

### 3. Update .env File
```env
# Add these lines:
DB_HOST=localhost
DB_NAME=rescuetime  
DB_USER=rescuetime_user
DB_PASSWORD=your_password
DB_PORT=5432
RESCUETIME_API_KEY=your_existing_key
```

### 4. Replace database.py
```bash
# Backup current database.py
cp database.py database_sqlite_backup.py

# Replace with PostgreSQL version
cp database_postgres.py database.py
```

### 5. Migrate Existing Data
```bash
# Export from SQLite
sqlite3 rescuetime.db ".dump" > rescuetime_backup.sql

# Convert and import to PostgreSQL (you may need to edit the SQL)
python migrate_data.py  # Script we can create if needed
```

### 6. Test the Migration
```bash
python main.py initdb
python -c "import database; print('PostgreSQL connection successful!')"
```

## Cloud PostgreSQL Options:
- **DigitalOcean Managed PostgreSQL**: $15/month
- **AWS RDS**: ~$20/month  
- **Heroku Postgres**: Free tier available
- **Supabase**: Free tier with 500MB

## Rollback Plan:
Keep `database_sqlite_backup.py` and your `rescuetime.db` file as backup.
