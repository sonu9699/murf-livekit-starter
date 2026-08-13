import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';
import fs from 'fs';

const execAsync = promisify(exec);

export async function GET() {
  try {
    const backendDir = path.resolve(process.cwd(), '../backend');
    
    // Quick path check
    const dbPath = path.join(backendDir, 'aarogya_memory.db');
    if (!fs.existsSync(dbPath)) {
      console.log('aarogya_memory.db not found, returning empty array');
      return NextResponse.json([]);
    }

    // Execute inline python command to load profiles
    const cmd = `uv run python -c "
import sqlite3, json, os, sys
sys.path.append('src')
import memory
db_path = memory.default_db_path()
if not os.path.exists(db_path):
    print('[]')
    sys.exit(0)
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    rows = conn.execute('SELECT * FROM callers ORDER BY updated_at DESC').fetchall()
    res = []
    for r in rows:
        d = dict(r)
        # Parse conditions JSON array if stored as string
        try:
            if isinstance(d.get('conditions'), str):
                d['conditions'] = json.loads(d['conditions'])
        except Exception:
            d['conditions'] = []
        res.append(d)
    print(json.dumps(res))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"`;

    const { stdout } = await execAsync(cmd, { cwd: backendDir });
    
    try {
      const data = JSON.parse(stdout.trim());
      if (data && data.error) {
        throw new Error(data.error);
      }
      return NextResponse.json(data || []);
    } catch (parseError) {
      console.error('Failed to parse Python database output:', stdout);
      return NextResponse.json({ error: 'Database read failed to parse', output: stdout }, { status: 500 });
    }
  } catch (error: any) {
    console.error('Error fetching patients:', error);
    return NextResponse.json({ error: 'Failed to retrieve patient directory', details: error.message || String(error) }, { status: 500 });
  }
}
