import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Resolve path to backend/calls.json
const jsonPath = path.resolve(process.cwd(), '../backend/calls.json');

export async function GET() {
  try {
    if (!fs.existsSync(jsonPath)) {
      return NextResponse.json([]);
    }
    const data = fs.readFileSync(jsonPath, 'utf8');
    const calls = JSON.parse(data);
    return NextResponse.json(calls);
  } catch (error) {
    console.error('Error reading calls:', error);
    return NextResponse.json({ error: 'Failed to read calls' }, { status: 500 });
  }
}
