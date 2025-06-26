// import { spawn } from 'child_process';
// import readline from 'readline';
// import path from 'path';
// import { v4 as uuidv4 } from 'uuid';
// import fs from 'fs';

// type RunOptions = {
//   photoPath: string;
//   platforms: string[];
//   description?: string;
//   useAI?: boolean;
//   styleChoice: number;
//   colorChoice?: number;
// };

// function buildPythonArgs(photoPath: string, platforms: string[], description?: string, useAI?: boolean): string[] {
//   const args = [photoPath, '--platforms', ...platforms];
//   if (description) args.push('--description', description);
//   if (useAI) args.push('--use-ai');
//   return args;
// }


// export async function runPythonScript({
//   photoPath,
//   platforms,
//   description,
//   useAI,
//   styleChoice,
//   colorChoice
// }: RunOptions): Promise<string> {




//   const args = buildPythonArgs(photoPath, platforms, description, useAI);

// //   console.log('Running Python script with arguments:', args);
// //   return 

  
//   const python = spawn('python', ['./ImageModule/main.py', ...args]);

//   const rl = readline.createInterface({ input: python.stdout! });

//   let sessionId: string | null = null;
//   let readyResolved = false;

//   return new Promise((resolve, reject) => {
//     python.stderr?.on('data', (data) => {
//       console.error('Error:', data.toString());
//     });

//     rl.on('line', (line) => {
//       console.log('[PYTHON]', line);

//       if (line.includes('Would you like to perform product photography enhancement?')) {
//         python.stdin.write('y\n');
//       } else if (line.includes('Enter the path to your logo image')) {
//         python.stdin.write('\n');
//       } else if (line.includes('Enter your choice (1-7):')) {
//         python.stdin.write(`${styleChoice}\n`);
//       } else if (styleChoice === 7 && line.includes('Enter your color choice (1-15):')) {
//         python.stdin.write(`${colorChoice || 1}\n`);
//       }

//       const match = line.match(/📋 Compiling caption for:\s*(\w+)_/);
//       if (match) {
//         sessionId = match[1];
//       }

//       if (line.includes('Ready-to-Use Content:') && sessionId && !readyResolved) {
//         readyResolved = true;
//         resolve(sessionId);
//         rl.close();
//         // python.kill();
//       }
//     });

//     python.on('exit', (code) => {
//       if (!readyResolved) reject(new Error(`Python exited with code ${code}`));
//     });
//   });
// }

import { spawn } from 'child_process';
import path from 'path';

type RunOptions = {
  photoPath: string;
  platforms: string[];
  description?: string;
  useAI?: boolean;
  styleChoice: number;
  colorChoice?: number;
};

function buildPythonArgs(photoPath: string, platforms: string[], description?: string, useAI?: boolean): string[] {
  const args = [photoPath, '--platforms', ...platforms];
  if (description) args.push('--description', description);
  if (useAI) args.push('--use-ai');
  return args;
}

export async function runPythonScript({
  photoPath,
  platforms,
  description,
  useAI,
  styleChoice,
  colorChoice
}: RunOptions): Promise<string> {

  const args = buildPythonArgs(photoPath, platforms, description, useAI);
  const python = spawn('python', ['./ImageModule/main.py', ...args]);

  let buffer = '';
  let sessionId: string | null = "123456";
  let readyResolved = false;

  return new Promise((resolve, reject) => {
    python.stdout.on('data', (data: Buffer) => {
      const text = data.toString();
      buffer += text;
      console.log('[PYTHON]', text)

      // Check for prompts and respond
      if (text.includes('Would you like to perform product photography enhancement?')) {
        python.stdin.write('y\n');
      } else if (text.includes('Enter the path to your logo image')) {
        python.stdin.write('\n');
      } else if (text.includes('Enter your choice (1-7):')) {
        python.stdin.write(`${styleChoice}\n`);
      } else if (styleChoice === 7 && text.includes('Enter your color choice (1-15):')) {
        python.stdin.write(`${colorChoice || 1}\n`);
      }

      // Extract session ID
        const uuidMatch2 = text.match(/📋 Compiled files:\s*\d+\.\s*([a-f0-9]+)_/i);
        if (uuidMatch2) {
        sessionId = uuidMatch2[1];
        console.log('[✅ SESSION ID FROM Compiled file name]', sessionId);
        }

        // Detect completion
        const normalized = text.replace(/\s+/g, ' ').trim();

        if (
        (text.includes('🎯 Ready-to-Use Content') || normalized.includes('Ready-to-Use Content')) &&
        sessionId &&
        !readyResolved
        ) {
        readyResolved = true;
        resolve(sessionId);
        // python.stdin.end();
        // python.kill(); // optional but safe cleanup
        }

            });

    python.stderr?.on('data', (data) => {
      console.error('[PYTHON ERROR]', data.toString());
    });

    python.on('exit', (code) => {
      if (!readyResolved) {
        console.error('[❌ PROCESS EXITED WITHOUT RESOLVING]');
    console.error('[DEBUG] Final sessionId:', sessionId);
    console.error('[DEBUG] Buffer so far:', buffer);
        reject(new Error(`Python process exited with code ${code}`));
      }
    });
  });
}
