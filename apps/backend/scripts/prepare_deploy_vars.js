const fs = require('fs');
const path = require('path');

const envPath = path.join(__dirname, '..', '.env');
const outputPath = path.join(__dirname, '..', 'deploy_env.json');

try {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const envVars = {};

    envContent.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
            const parts = trimmed.split('=');
            if (parts.length >= 2) {
                const key = parts[0].trim();
                const value = parts.slice(1).join('=').trim();
                envVars[key] = value;
            }
        }
    });

    // Add overrides for Cloud Run
    envVars['USE_LOCAL_REDIS'] = 'False';
    envVars['PYTHONUNBUFFERED'] = '1';
    envVars['DEBUG'] = 'False';

    const output = Object.entries(envVars)
        .map(([k, v]) => `${k}=${v}`)
        .join(',');

    // Write as JSON map or key-value file?
    // gcloud run deploy --env-vars-file=deploy_env.json expects a YAML or JSON dict.
    fs.writeFileSync(outputPath, JSON.stringify(envVars, null, 2));
    console.log(`Successfully created ${outputPath} with ${Object.keys(envVars).length} variables.`);

} catch (err) {
    console.error('Error processing .env:', err);
    process.exit(1);
}
