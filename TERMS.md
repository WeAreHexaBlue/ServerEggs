# Terms of Service for **Server Eggs**

*(**Disclaimer**: These terms were drafted with AI assistance because the developers don't have the resources to hire a lawyer for a hobby Discord bot. They are not legal advice.)*

**Last Updated:** September 30, 2026

By adding **Server Eggs** ("the Bot") to a Discord server, or by using any of its features, you agree to these Terms of Service ("Terms"). If you do not agree, do not use the Bot. See Section 11 for how acceptance works.

## 1. Description of Service

**Server Eggs** is a Discord bot that lets users create, share, collect, search, and battle content snippets called "**Egg**s" — text, images, video, audio, or links. **Egg**s are retrievable across every server the Bot is installed in. **Egg**s are also linked back to the server they originated from, including that server's name and invite link, which gives the Bot a server-discovery function.

The Bot is provided free of charge, with an optional paid **Supporter** entitlement (Section 8).

## 2. Eligibility

You must be at least **13 years old** (or the minimum age required to use Discord in your country, if higher) to use the Bot. The digital-consent age under the GDPR can be up to 16 in some EU member states — see Section 9 of the [Privacy Policy](PRIVACY.md). If you are under the age of majority where you live, you confirm you have permission from a parent or guardian.

By using the Bot you confirm you meet these requirements.

## 3. Your Content and Conduct

You are solely responsible for everything you create through the Bot. By creating an **Egg** you agree:

*   **Discord compliance.** All content must comply with [Discord's Terms of Service](https://discord.com/terms) and [Community Guidelines](https://discord.com/guidelines).
*   **Ownership and licensing.** You may only submit content you own or have the legal right to use, modify, and distribute. Uploading someone else's copyrighted work without permission is prohibited. By creating an **Egg**, you grant the Bot a non-exclusive, worldwide, royalty-free licence to store, display, and redistribute that **Egg** across all servers where the Bot is installed — that is what the Bot is for. You retain ownership of your content.
*   **Other people's personal data.** You must not publish another person's personal data (photos, names, contact details, location, and the like) in an **Egg** unless you have a lawful basis to do so. Where you do, you act as the data controller for that data and you are responsible for having a lawful basis and responding to that person's rights requests.
*   **NSFW content.** Explicit content may only be created in Discord channels that are properly age-restricted, and may only be configured as retrievable in such channels. Server admins control this via `/config allowed-ratings` and `/config channel-rating`.
*   **Prohibited content.** You may not use the Bot to distribute CSAM, illegal content, malware, spam, harassment, doxxing, non-consensual intimate imagery, or content that promotes violence.
*   **No abuse of the service.** Do not attempt to circumvent rate limits, manipulate leaderboards or battles, abuse reporting features, or probe the Bot's infrastructure.

### 3.1 Automated safety scanning

Every uploaded attachment is scanned by a third-party safety service (**Arachnid Shield**) to detect child sexual abuse material and other prohibited content. By uploading media to the Bot, you consent to that media being transmitted to this service for scanning. **Egg**s with unscanned media are stored in quarantine and stay invisible to other users until the scan clears. A match results in deletion of the **Egg** and an immediate ban from creating **Egg**s, subject to human review on request (Section 4).

### 3.2 Who is responsible for uploaded content

This is the split, stated plainly:

*   **You are responsible for what you upload.** You are the author and the originator of your **Egg**s. You warrant that your content is lawful, that you own it or have the right to use it, and that it does not infringe anyone's rights. If it does, **the claim lies against you, not against the developers.** You must take the consequences of your own uploads, including any claim, takedown, or dispute arising from them, and you agree to indemnify the developers for them (Section 9).
*   **The developers are not the author or publisher of your content.** The developers do not originate, select, or approve **Egg**s before they appear. Their role is to operate the technical service that stores and displays what *you* submitted.
*   **The developers remain responsible for running the service.** Responsibility for the Bot's operation is theirs and cannot be transferred to you: responding to valid notices and reports, moderating content once it is brought to their attention, the security of the database, and compliance with data-protection law. Operating a hosting service in this way is what earns the legal protection commonly called "safe harbour" (in the EU, Article 14 of the E-Commerce Directive; in the US, §512 of the DMCA) — protection which **depends on acting on notice**, and which is lost if a valid takedown or report is ignored.

In short: the uploader carries the content; the developers carry the service.

## 4. Moderation, Reports, and Bans

We moderate the Bot to keep it safe:

*   **Reports.** Users can report an **Egg** with a written reason. Reports go to a private moderator channel, where moderators can ignore the report, change the **Egg**'s rating or language, delete the **Egg**, or delete it and ban the creator. Reporters are notified of the outcome by DM.
*   **Content removal.** We may delete any **Egg** at any time, with or without notice, including for storage, health, or policy reasons.
*   **Server-side blocking.** Server managers can block specific **Egg**s from appearing in their server using `/filter`.
*   **Bans.** We may revoke your ability to create **Egg**s or vote in battles for violations of these Terms, for safety-scan matches, or for repeated reports. You may appeal a ban by contacting us (Section 10); **reinstatement is entirely at our discretion, and you may always ask for human review of an automated decision.**
*   **Server removal.** We may remove the Bot from any server that uses it in violation of these Terms.

## 5. Copyright Claims and Takedowns

We respect intellectual property rights. If your copyrighted work has been uploaded as an **Egg** without authorization, contact us at:

*   **Email:** [flamey@hexa.blue](mailto:flamey@hexa.blue) — preferred, it leaves a record
*   **Discord:** [actuallyflamey](https://discord.com/users/450678229192278036)

Include:

1.  A description of the copyrighted work you own.
2.  The exact **Egg** ID or content in question.
3.  Your contact information and a good-faith statement that the use is not authorized.
4.  A statement, under penalty of perjury, that the information is accurate and you are the rights holder or authorized to act for them.

On a valid request we will remove or disable access to the content promptly. Users who repeatedly upload infringing material will be permanently banned. Counter-notices from the uploader may be sent through the same channels.

## 6. Server Administration

Server administrators are responsible for configuring the Bot appropriately for their community. Relevant controls:

*   **`/config privacy public:False`** — hides your server's invite link from **Egg**s created there (requires Manage Server).
*   **`/config log`** — sets a channel that receives create/edit logs. Anyone with access to that channel will see user display names, usernames, and **Egg** IDs.
*   **`/config allowed-ratings`** and **`/config channel-rating`** — control which content ratings are allowed, and where.
*   **`/filter`** — blocks specific **Egg**s server-wide.

By adding the Bot to your server, you confirm you have the authority to do so and to bind that server to these Terms.

## 7. Licence and Intellectual Property

The Bot's source code is open source under the **GNU General Public License v3.0 (GPL-3.0)**. You are free to view, modify, and redistribute the code under that licence.

However, the official hosted instance of **Server Eggs**, its database, its stored media, and its official branding and icons remain the property of the developers. GPL-3.0 covers the code, not the hosted service or its data. Self-hosting produces your own separate instance and database.

## 8. Payments, Supporter, and Donations

*   **Supporter entitlement** is purchased through **Discord App Subscriptions**. Discord handles the payment, billing, and any refund decisions under [Discord's own terms](https://discord.com/terms). The entitlement unlocks the Daily **Egg** DM feature and nothing else.
*   **Ko-fi donations** at [ko-fi.com/hexablue](https://ko-fi.com/hexablue) are voluntary gifts and do not purchase any entitlement, feature, or refund right.
*   We do not process or store your payment details — those never touch our systems, so no payment data appears in our Privacy Policy.
*   If the Daily **Egg** feature is discontinued, existing entitlements are not refunded by us; take refund requests to Discord.

## 9. Disclaimer and Limitation of Liability

The Bot is provided **"AS IS"**, without warranty of any kind, express or implied, including fitness for a particular purpose and non-infringement.

To the maximum extent permitted by law, the developers shall not be liable for any indirect, incidental, special, consequential, or exemplary damages, or for any loss of data, content, profits, or server availability, arising out of or in connection with your use of the Bot.

We do not guarantee 100% uptime, and we do not guarantee permanent storage of your **Egg**s. Content may be lost due to deletion, moderation, technical failure, or service shutdown.

You agree to indemnify and hold harmless the developers from any claims arising from (a) your use of the Bot, (b) your violation of these Terms, or (c) your violation of any third-party right, including copyright, privacy, or property rights, in connection with the **Egg**s you create.

Nothing in these Terms limits liability that cannot be limited under applicable law, and nothing in these Terms affects your statutory rights as a consumer under the laws of your country of residence.

## 10. Contact

*   **Email:** [flamey@hexa.blue](mailto:flamey@hexa.blue) — legal notices, copyright, bans, privacy
*   **Discord:** [actuallyflamey](https://discord.com/users/450678229192278036)
*   **GitHub:** https://github.com/WeAreHexaBlue/ServerEggs

## 11. Acceptance, Changes, and Termination

**How you accept.** These Terms are presented before use and acceptance is **passive**: by inviting the Bot to a server, or by using any of its commands or features, you are treated as having accepted them. The full text is always available at the repository's `TERMS.md`, and links to these Terms and the Privacy Policy are published in the Discord Developer Portal listing for the Bot. If you do not agree, do not use the Bot.

**Changes.** We may update these Terms at any time. The "Last Updated" date at the top will change when we do. Material changes will be announced in our support server or through the Bot where practical. Continued use of the Bot after a change constitutes acceptance of the updated Terms. If you do not accept a change, stop using the Bot and, if applicable, exercise your erasure rights under the Privacy Policy.

**Termination.** You may stop using the Bot at any time. We may suspend or terminate your access to the Bot at our discretion, with or without notice, including for violations of these Terms.

---

See also: [**Privacy Policy**](PRIVACY.md) · [Source Code (GPL-3.0)](https://github.com/WeAreHexaBlue/ServerEggs) · [Discord Terms](https://discord.com/terms) · [Discord Community Guidelines](https://discord.com/guidelines)
