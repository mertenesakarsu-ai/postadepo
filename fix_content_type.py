#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def fix_content_type():
    # Load environment variables
    load_dotenv('/app/backend/.env')
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Count emails without content_type first
        count = await db.emails.count_documents({'content_type': {'$exists': False}})
        print(f'Found {count} emails without content_type field')
        
        if count > 0:
            # Update all emails that don't have content_type field
            result = await db.emails.update_many(
                {'content_type': {'$exists': False}},
                {'$set': {'content_type': 'text'}}
            )
            print(f'Updated {result.modified_count} emails with content_type field')
        
        # Verify the update
        demo_user = await db.users.find_one({'email': 'demo@postadepo.com'})
        if demo_user:
            emails = await db.emails.find({'user_id': demo_user['id']}).limit(3).to_list(length=None)
            print(f'Verification - Found {len(emails)} emails for demo user:')
            for i, email in enumerate(emails):
                print(f'  Email {i+1}: content_type = {email.get("content_type", "MISSING")}')
        
        print("Content type fix completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_content_type())