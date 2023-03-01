module.exports = {
  serverRuntimeConfig: {
    // Switch to enable / disable mandatory Firebase authentication
    require_auth: false,
    // Google Secret Manager secret that holds the Firebase admin credentials.
    // Can have an arbitrary value as long as the above option is set to `false`.
    secret_name: 'TODO',
    // Switch to remove navigation bar and "give it a whirl" button from home
    // page. That would be set to `true` if the backend isn't up.
    is_deployed: true,
  },
  distDir: 'build',
};
