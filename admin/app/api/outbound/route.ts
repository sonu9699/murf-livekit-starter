import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(req: NextRequest) {
  try {
    const { to, name, scenario, babyAge } = await req.json();
    if (!to) {
      return NextResponse.json({ error: 'Missing "to" (phone number or SIP ID)' }, { status: 400 });
    }

    const backendDir = path.resolve(process.cwd(), '../backend');
    
    // Sanitize arguments to prevent shell command injection
    const sanitize = (val: string) => val.replace(/[^a-zA-Z0-9_+\-@.]/g, '');
    const cleanTo = to.trim().replace(/[^a-zA-Z0-9_+\-@.:]/g, '');
    const cleanName = name ? sanitize(name.trim()) : 'Rahul';
    const cleanScenario = scenario === 'triage_followup' ? 'triage_followup' : 'vaccination_reminder';
    const cleanBabyAge = Number(babyAge) || 2;

    const cmd = `uv run python src/dial_outbound.py --to "${cleanTo}" --name "${cleanName}" --scenario "${cleanScenario}" --baby-age ${cleanBabyAge}`;
    console.log(`Executing outbound dial: ${cmd} in ${backendDir}`);
    
    const { stdout, stderr } = await execAsync(cmd, { cwd: backendDir });
    console.log('Outbound dial stdout:', stdout);
    if (stderr) {
      console.warn('Outbound dial stderr:', stderr);
    }

    return NextResponse.json({ 
      success: true, 
      message: `Outbound call initiated to ${cleanTo}`,
      output: stdout 
    });
  } catch (error: any) {
    console.error('Error placing outbound call:', error);
    return NextResponse.json({ 
      error: 'Failed to place outbound call', 
      details: error.message || String(error)
    }, { status: 500 });
  }
}
