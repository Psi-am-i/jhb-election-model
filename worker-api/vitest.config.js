// Two test projects:
//   node     test/node/*.test.js    build-time checks that need the filesystem
//   workers  test/*.test.js         the Worker, inside workerd, with local D1 and R2
//
// Nothing here is a secret. The session signing key is random per run; the
// provider "client ids" are fixed fakes that no provider has issued.
import { defineConfig } from "vitest/config";
import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-pool-workers";
import { randomBytes, generateKeyPairSync } from "node:crypto";

export default defineConfig(async () => {
  const migrations = await readD1Migrations("./migrations");
  return {
    test: {
      projects: [
        { test: { name: "node", include: ["test/node/**/*.test.js"], environment: "node" } },
        {
          plugins: [cloudflareTest({
            wrangler: { configPath: "./wrangler.jsonc" },
            miniflare: {
              bindings: {
                TEST_MIGRATIONS: migrations,
                SESSION_SIGNING_KEY: randomBytes(32).toString("hex"),
                TURNSTILE_REQUIRED: "false",
                GOOGLE_CLIENT_ID: "fake-google-client", GOOGLE_CLIENT_SECRET: "fake",
                APPLE_SERVICE_ID: "fake.apple.service", APPLE_TEAM_ID: "FAKETEAM", APPLE_KEY_ID: "FAKEKEY",
                APPLE_PRIVATE_KEY: generateKeyPairSync("ec", { namedCurve: "P-256" }).privateKey.export({ type: "pkcs8", format: "pem" }),
                X_CLIENT_ID: "fake-x", X_CLIENT_SECRET: "fake",
                MICROSOFT_CLIENT_ID: "fake-ms", MICROSOFT_CLIENT_SECRET: "fake",
                FACEBOOK_APP_ID: "fake-fb", FACEBOOK_APP_SECRET: "fake-fb-app-secret-for-tests",
              },
              // The seat service is a TEST DOUBLE (test/fake-seats.js), NOT the seat law.
              serviceBindings: { SEATS: async req => (await import("./test/fake-seats.js")).fakeSeats(req) },
            },
          })],
          test: { name: "workers", include: ["test/*.test.js"], setupFiles: ["./test/apply-migrations.js"] },
        },
      ],
    },
  };
});
