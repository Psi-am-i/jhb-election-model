// Outgoing mail: the post-election message and the one contact-confirmation
// link. Message bodies are here so their wording is reviewable in one place.
//
// Transport: Cloudflare Email Service through a `send_email` binding named
// EMAIL, sending from MAIL_FROM (a var; an address on a verified sending
// domain). NEITHER IS CONFIGURED: no binding exists in wrangler.jsonc and
// MAIL_FROM is empty, so sendMail reports a TRANSIENT failure and nothing is
// sent. The binding's shape (send({to, from, subject, text}) -> {messageId};
// errors thrown with a string `code`) is from the Email Service Workers API
// docs as of 2026-09-29.
//
// Result classes, which the callers depend on:
//   { sent: true }                       handed to the mail service
//   { sent: false, permanent: true }     THIS recipient cannot be mailed
//                                        (suppressed after a hard bounce or
//                                        complaint): recorded as undeliverable
//   { sent: false, permanent: false }    anything else, including a missing
//                                        binding or a sender-side error: try
//                                        again later. A sender-side fault
//                                        affects every recipient, so it must
//                                        never be read as "undeliverable".
//
// There is no SMS route. No provider in the owner's list returns a phone number
// at the scopes requested, so a phone contact is never collected today.

export const POST_ELECTION_WORDING_VERSION = "draft-2026-09-28";

// Email Service error codes that describe the recipient, not us. Kept narrow on
// purpose: a code missing here costs a retry; a code wrongly here marks a
// reader undeliverable and lets the deletion run proceed without them.
export const PERMANENT_CODES = new Set(["E_RECIPIENT_SUPPRESSED"]);

export function postElectionMessage({ deleteUrl, notifyUrl, deletionDate }) {
  return {
    subject: "Your Johannesburg prediction: delete your data, or hear about the next election?",
    text:
`Thank you for making a prediction at joburg.whysoserious.city.

The election is over. We will not keep your details without a reason, so please choose one:

  Delete my data now:                 ${deleteUrl}
  Tell me about the next election:    ${notifyUrl}

If you do not choose, we will delete your account, your predictions and your contact details on ${deletionDate}.
If you ask to hear about the next election, we keep only your sign-in id and this address, and delete your predictions.`,
  };
}

export function confirmationMessage({ confirmUrl }) {
  return {
    subject: "Confirm your email address for joburg.whysoserious.city",
    text:
`Someone signed in at joburg.whysoserious.city and asked us to use this address.

If it was you, confirm it here:

  ${confirmUrl}

If you do nothing, we do not keep this address and will not email it again.`,
  };
}

export async function sendMail(env, { to, subject, text }) {
  if (!env.EMAIL || !env.MAIL_FROM) {
    console.log(JSON.stringify({ msg: "mail not sent: transport not configured", binding: Boolean(env.EMAIL), from: Boolean(env.MAIL_FROM) }));
    return { sent: false, permanent: false, reason: "mail transport not configured" };
  }
  try {
    await env.EMAIL.send({ to, from: env.MAIL_FROM, subject, text });
    return { sent: true };
  } catch (e) {
    const code = typeof e?.code === "string" ? e.code : "unknown";
    // The recipient's address is never logged.
    console.error(JSON.stringify({ msg: "mail send failed", code }));
    return { sent: false, permanent: PERMANENT_CODES.has(code), reason: code };
  }
}
