import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(req: NextRequest) {
  try {
    const backendDir = path.resolve(process.cwd(), '../backend');
    
    // File paths
    const dbPath = path.join(backendDir, 'aarogya_memory.db');
    const callsJsonPath = path.join(backendDir, 'calls.json');
    const escalationsJsonPath = path.join(backendDir, 'escalations.json');

    // 1. Delete SQLite DB file if it exists (recreated automatically on next query)
    if (fs.existsSync(dbPath)) {
      try {
        fs.unlinkSync(dbPath);
        console.log('Successfully deleted aarogya_memory.db');
      } catch (err) {
        console.error('Failed to unlink DB file, attempting to clear tables instead:', err);
      }
    }

    // 2. Clear calls.json
    fs.writeFileSync(callsJsonPath, '[]', 'utf8');
    console.log('Reset calls.json');

    // 3. Clear escalations.json
    fs.writeFileSync(escalationsJsonPath, '[]', 'utf8');
    console.log('Reset escalations.json');

    return NextResponse.json({ success: true, message: 'All database and logs reset successfully.' });
  } catch (error: any) {
    console.error('Error resetting database logs:', error);
    return NextResponse.json({ error: 'Failed to reset data', details: error.message || String(error) }, { status: 500 });
  }
}
