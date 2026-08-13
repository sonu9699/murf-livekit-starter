import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Resolve path to backend/escalations.json
const jsonPath = path.resolve(process.cwd(), '../backend/escalations.json');

export async function GET() {
  try {
    if (!fs.existsSync(jsonPath)) {
      return NextResponse.json([]);
    }
    const data = fs.readFileSync(jsonPath, 'utf8');
    const escalations = JSON.parse(data);
    return NextResponse.json(escalations);
  } catch (error) {
    console.error('Error reading escalations:', error);
    return NextResponse.json({ error: 'Failed to read escalations' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const { id, status } = await req.json();
    if (!id || !status) {
      return NextResponse.json({ error: 'Missing id or status' }, { status: 400 });
    }

    // Try to update SQLite database via python script
    try {
      const backendDir = path.resolve(process.cwd(), '../backend');
      const cmd = `uv run python -c "import sys; sys.path.append('src'); import escalation; escalation.update_status('${id}', '${status}')"`;
      await execAsync(cmd, { cwd: backendDir });
      console.log(
        `Successfully updated escalation ${id} status to ${status} in SQLite via Python.`
      );
    } catch (dbError) {
      console.error(
        'Failed to update status in SQLite database via Python, falling back to JSON only:',
        dbError
      );

      // Fallback: Manually update in JSON if python execution failed
      if (fs.existsSync(jsonPath)) {
        const data = fs.readFileSync(jsonPath, 'utf8');
        const escalations = JSON.parse(data);
        const index = escalations.findIndex((esc: { id: string }) => esc.id === id);
        if (index !== -1) {
          escalations[index].status = status;
          fs.writeFileSync(jsonPath, JSON.stringify(escalations, null, 2), 'utf8');
        }
      }
    }

    // Return the updated JSON array
    if (fs.existsSync(jsonPath)) {
      const data = fs.readFileSync(jsonPath, 'utf8');
      return NextResponse.json(JSON.parse(data));
    }
    return NextResponse.json([]);
  } catch (error) {
    console.error('Error updating escalation status:', error);
    return NextResponse.json({ error: 'Failed to update escalation status' }, { status: 500 });
  }
}
