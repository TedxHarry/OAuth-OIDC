import { OktaAuth } from '@okta/okta-auth-js';

const CONFIG_KEY = 'day07_config';

const configSection = document.getElementById('config-section');
const appSection = document.getElementById('app-section');
const configForm = document.getElementById('config-form');
const issuerInput = document.getElementById('issuer');
const clientIdInput = document.getElementById('client-id');
const statusElement = document.getElementById('status');
const loginButton = document.getElementById('login-button');
const clearButton = document.getElementById('clear-button');
const resetButton = document.getElementById('reset-button');

let oktaAuth = null;

function normalizeIssuer(value) {
  return value.trim().replace(/\/$/, '');
}

function readConfig() {
  const raw = sessionStorage.getItem(CONFIG_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    sessionStorage.removeItem(CONFIG_KEY);
    return null;
  }
}

function saveConfig(config) {
  sessionStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}

function safeTokenSummary(idToken, accessToken, refreshToken) {
  return {
    authenticated_for_lab: Boolean(idToken),
    id_token_present_in_browser_token_manager: Boolean(idToken),
    access_token_present_in_browser_token_manager: Boolean(accessToken),
    refresh_token_present_in_browser_token_manager: Boolean(refreshToken),
    raw_tokens_rendered_to_page: false,
    token_manager_storage: 'sessionStorage',
    oauth_client_location: 'browser JavaScript'
  };
}

async function renderStatus() {
  if (!oktaAuth) {
    return;
  }

  const idToken = await oktaAuth.tokenManager.get('idToken');
  const accessToken = await oktaAuth.tokenManager.get('accessToken');
  const refreshToken = await oktaAuth.tokenManager.get('refreshToken');

  statusElement.textContent = JSON.stringify(
    safeTokenSummary(idToken, accessToken, refreshToken),
    null,
    2
  );
}

async function initializeApp(config) {
  configSection.hidden = true;
  appSection.hidden = false;

  oktaAuth = new OktaAuth({
    issuer: config.issuer,
    clientId: config.clientId,
    redirectUri: window.location.origin + '/',
    scopes: ['openid', 'profile', 'email'],
    pkce: true,
    tokenManager: {
      storage: 'sessionStorage'
    }
  });

  // Exposed only for this training lab so the learner can inspect the SDK
  // object from DevTools. Do not use global variables like this as a normal
  // production application design.
  window.day07OktaAuth = oktaAuth;

  if (oktaAuth.isLoginRedirect()) {
    statusElement.textContent = 'OAuth callback detected. Processing...';

    try {
      const result = await oktaAuth.token.parseFromUrl();
      oktaAuth.tokenManager.setTokens(result.tokens);

      window.history.replaceState(
        {},
        document.title,
        window.location.origin + '/'
      );
    } catch (error) {
      statusElement.textContent =
        'OAuth callback processing failed:\n' +
        (error && error.message ? error.message : String(error));
      throw error;
    }
  }

  oktaAuth.authStateManager.subscribe(async () => {
    await renderStatus();
  });

  await oktaAuth.start();
  await oktaAuth.authStateManager.updateAuthState();
  await renderStatus();

  loginButton.addEventListener('click', async () => {
    await oktaAuth.signInWithRedirect({
      originalUri: window.location.origin + '/'
    });
  });

  clearButton.addEventListener('click', async () => {
    oktaAuth.tokenManager.clear();
    await oktaAuth.authStateManager.updateAuthState();
    await renderStatus();
  });

  resetButton.addEventListener('click', async () => {
    if (oktaAuth) {
      oktaAuth.stop();
    }

    sessionStorage.clear();
    window.location.replace(window.location.origin + '/');
  });
}

configForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const config = {
    issuer: normalizeIssuer(issuerInput.value),
    clientId: clientIdInput.value.trim()
  };

  if (!config.issuer.startsWith('https://')) {
    statusElement.textContent =
      'Use the full HTTPS Okta issuer, for example https://integrator-123456.okta.com';
    return;
  }

  saveConfig(config);
  window.location.reload();
});

const config = readConfig();

if (config) {
  initializeApp(config).catch((error) => {
    console.error(error);
  });
} else {
  configSection.hidden = false;
  appSection.hidden = true;
}
