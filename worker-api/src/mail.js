// ⛔ STUB. Outgoing mail: the post-election message and contact verification.
//
// Nothing is sent. The intended transport is Cloudflare Email Service through
// a `send_email` binding named EMAIL, from a verified sender on the site's
// domain; its exact send() shape must be taken from the current Email Service
// docs when this is wired, not from this comment. Until then sendMail reports
// { sent: false } and the caller treats the message as not delivered.
//
// There is no SMS route. No provider in the owner's list returns a phone number
// at the scopes requested, so a phone contact is never collected today; the
// schema allows one so a later provider can supply it.
//
// Message bodies are here so their wording is reviewable in one place.

export const POST_ELECTION_WORDING_VERSION = "draft-2026-09-28";

export function postElectionMessage({ deleteUrl, notifyUrl, deletionDate }) {
  return {
    subject: "Your Johannesburg forecast: delete your data, or hear about the next election?",
    text:
`Thank you for making a forecast at joburg.whysoserious.city.

The election is over. We will not keep your details without a reason, so please choose one:

  Delete my data now:                 ${deleteUrl}
  Tell me about the next election:    ${notifyUrl}

If you do not choose, we will delete your account, your forecasts and your contact details on ${deletionDate}.
If you ask to hear about the next election, we keep only your sign-in id and this address, and delete your forecasts.`,
  };
}

export async function sendMail(env, { to, subject, text }) {
  void to; void subject; void text;
  console.log(JSON.stringify({ msg: "mail stub: not sent", binding: Boolean(env.EMAIL) }));
  return { sent: false, reason: "mail transport not wired (src/mail.js is a stub)" };
}
