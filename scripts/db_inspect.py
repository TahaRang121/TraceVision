import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect("postgresql://postgres:postgrespassword@localhost:5433/tracevision")
    
    # 1. Check columns of search_results
    cols = await conn.fetch("""
        SELECT column_name, is_nullable, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'search_results';
    """)
    print("search_results columns:")
    for col in cols:
        print(f"  - {col['column_name']}: {col['data_type']}, nullable={col['is_nullable']}")

    # If video_id is not nullable, alter it
    for col in cols:
        if col['column_name'] == 'video_id' and col['is_nullable'] == 'NO':
            print("Altering video_id to DROP NOT NULL...")
            await conn.execute("ALTER TABLE search_results ALTER COLUMN video_id DROP NOT NULL;")
            print("Successfully altered video_id to DROP NOT NULL.")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())

