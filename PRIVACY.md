# Privacy Policy for **Server Eggs**

*(**Disclaimer**: This policy was drafted with AI assistance because the developers don't have the resources to hire a lawyer for a hobby Discord bot. It is written to describe what the code actually does, but it is not legal advice.)*

**Last Updated:** September 30, 2026

This Privacy Policy explains what **Server Eggs** ("the Bot", "we", "us", or "our") collects, why it collects it, who can see it, how long we keep it, and what rights you have over it. It applies when you add the Bot to a Discord server, when a server admin configures it, and when you interact with any of its features.

## 1. Who Is Responsible for Your Data (Data Controller)

The data controller for all personal data described in this policy is the developer of **Server Eggs**, an individual established in the European Union / EEA, contactable at:

*   **Email:** [flamey@hexa.blue](mailto:flamey@hexa.blue)
*   **Discord:** [actuallyflamey](https://discord.com/users/450678229192278036)

Discord is a separate, independent controller for the data it holds about your Discord account; see [Discord's Privacy Policy](https://discord.com/privacy).

## 2. What We Collect

### 2.1 Account data
Created automatically the first time you interact with the Bot:
*   **Your Discord User ID** (the immutable numeric ID, not your username).
*   **Your language preference** (set via `/config lang` or auto-detected).
*   **Your public/private profile flag** (set via `/config privacy`).
*   **Your explicit-content DM consent flag** (only set if you use the Supporter daily **Egg** feature).
*   Your last daily **Egg** timestamp (Supporter feature only).
*   **Your ban status**, set if the safety scan or a moderator action flags you.
*   The list of **Egg**s you have collected.

Your username and display name are **not stored**. They are read live from Discord when the Bot needs to display them.

### 2.2 Server (guild) data
When the Bot is added to a server, and whenever an admin runs `/config`:
*   **Guild ID**, server **description**, and an **invite link** (created by the Bot automatically on join).
*   **Language settings**, including whether **Egg**s in other languages are allowed.
*   **Content-rating configuration** (which ratings are allowed, and which channels map to which rating).
*   **A log channel ID**, if the admin sets one via `/config log`.
*   **A join-button setting** and **battle timing**.
*   **The server's blocklist** of **Egg**s (set via `/filter`).

### 2.3 Content you create ("**Egg**s")
*   **Text** you type (up to 4,000 characters).
*   **Attachments you upload** (images, video, audio), stored as files on our server. Images are re-encoded to WebP for storage.
*   **Links you submit**, and media we resolve from those links (e.g. a YouTube or Twitter URL).
*   **A content hash** of your attachment, used to detect duplicate uploads.
*   **A content rating** (SAFE / QUESTIONABLE / EXPLICIT).
*   **Creator and origin-server references**, plus creation and edit timestamps.
*   **A `secret` flag**, if you mark the **Egg** as secret.

### 2.4 Activity data
*   **Battles:** the two **Egg**s involved, the challenger's user ID, the channel and message IDs, timing, and outcome.
*   **Battle votes:** your user ID and which side you voted for (one vote per user per battle).
*   **Reports:** your user ID, the reported **Egg**'s ID, and your reason (up to 200 characters).

### 2.5 Data we do **not** collect
*   **We do not read your messages.** The Bot runs without Discord's message-content intent and has no message listener. The only exception is the `eggify` right-click context menu, which reads the single message you explicitly choose to convert.
*   We do not collect your email, phone number, real name, IP address, or payment details.
*   We do not use third-party analytics, tracking, or advertising SDKs.
*   We do not build profiles of you beyond the **Egg**-creation, collection, battle, and report records described above.

### 2.6 Temporary technical data
*   **Rate limiting:** we keep an in-memory counter of recent commands per user and per server. This lives in RAM only, is not written to disk, and is wiped whenever the Bot restarts.
*   **Language cache:** a short-lived in-memory cache of language preferences, also wiped on restart.
*   **Media processing:** attachments are written to temporary files for scanning and are deleted immediately afterwards. Uploaded media is stored in quarantine, invisible to other users, until the safety scan clears.

## 3. Why We Process Your Data (Legal Bases)

Under the GDPR, each purpose needs its own legal basis under Article 6. Ours are:

| Purpose | Data used | Legal basis |
|---|---|---|
| Providing the Bot: creating, editing, deleting, searching and retrieving **Egg**s, battles, configuration | User ID, guild config, **Egg** content, activity data | **Art. 6(1)(b)** — performance of a contract, i.e. the service you asked for |
| Displaying attribution, leaderboards, and cross-server sharing | User ID; display name/username read live from Discord | **Art. 6(1)(f)** — legitimate interest in making the sharing feature function as advertised |
| Server discovery (origin server name + invite link on an **Egg**) | Guild name, invite link | **Art. 6(1)(f)** — legitimate interest; can be switched off with `/config privacy public:False` |
| Moderation: reports, bans, filtering, moderator review | Reports, ban flag, guild blocklist | **Art. 6(1)(f)** — legitimate interest in keeping the service safe |
| Scanning uploaded media for child sexual abuse material | Your media bytes, sent to Arachnid Shield | **Art. 6(1)(c)** legal obligation and **Art. 6(1)(d)** vital interests; such material is special-category data processed under **Art. 9(2)** on those grounds |
| Abuse prevention via rate limiting | In-memory counters | **Art. 6(1)(f)** — legitimate interest in service stability |
| Storing your language preference | `lang` field | **Art. 6(1)(b)** — part of the service |
| Sending you explicit-content Daily **Egg**s | `allow_explicit_dms` flag | **Art. 6(1)(a)** — your consent, given via the Yes/No prompt and withdrawable at any time |
| Sending you the Daily **Egg** you paid for | `last_daily_at` | **Art. 6(1)(b)** — performance of the Supporter entitlement |
| Sending occasional donation / store messages | User ID | **Art. 6(1)(f)** — legitimate interest; **opt out any time** by contacting us (see Section 6) |

Where we rely on **Art. 6(1)(f)**, we have assessed that your interest in using a public content-sharing bot is not overridden by our interest in operating it, and you can object as described in Section 8.

## 4. Third-Party Services and International Transfers

This is the part most policies hide. Here is exactly what leaves our server:

*   **Discord.** Everything you see in the Bot happens through Discord's API. Discord, Inc. is established outside the EEA; transfers are covered by Discord's own safeguards (including the EU–U.S. Data Privacy Framework where applicable) and its [Privacy Policy](https://discord.com/privacy).
*   **Arachnid Shield (`shield.projectarachnid.com`).** Uploaded media is stored in a quarantined state, invisible to other users, and sent to this third-party safety service so that child sexual abuse material and other prohibited content can be detected. **Your raw media bytes are transmitted to them for this check.** The operator is established outside the EEA; the transfer is necessary for compliance with legal obligations and for reasons of substantial public interest. If a match is found, the **Egg** is deleted and your account is banned from creating **Egg**s. See [Project Arachnid](https://projectarachnid.com/).
*   **Outbound URL fetches.** When you submit a link, we fetch that URL (and sometimes its Open Graph metadata) to resolve the embeddable media. The owner of that site sees a normal HTTP request from our server.
*   **Tenor, GitHub, Weblate, Ko-fi.** Used only for GIF URL normalization, loading our own branding images, community translations, and the donation page respectively. We do not send your user ID to these services in connection with your content.

**We do not sell your data.** We do not share your data with advertisers, data brokers, or any other third parties beyond the services listed above. Because the Bot lives entirely inside Discord, there are no other recipients of your personal data.

## 5. Who Can See What

**Server Eggs** is a **cross-server** application. Content is deliberately shared:

*   **Egg**s are **globally visible.** Any user on any server where the Bot is installed can retrieve any non-secret **Egg** you create, along with your **display name**, **username**, a link to your **Discord profile**, your **server's name**, and (unless disabled) your **server's invite link**.
*   **Leaderboards** (`/leaderboard`) publicly show your **display name**. Your **username** is only included if you set your profile to public.
*   **Log channels.** If a server admin runs `/config log`, every create/edit action is posted to that channel, including your display name, username, and the **Egg** ID. This is visible to everyone with access to that channel.
*   **Report channel.** Reports are sent to a private channel visible only to the Bot's moderators, including your **username, user ID, and reason**. This is required so moderators can contact you about the outcome.
*   **Moderators of the developers' server** can view all reports and act on them. Server managers can act on reports relayed to their own log channel.

Please do **not** put other people's personal data in an **Egg**. If you upload someone else's photo, name, or other personal information, you are acting as the controller for that data — see the Terms of Service.

## 6. Messages We Send You

The Bot may send you direct messages:

*   **Report receipts** when you submit a report, and **report outcome notifications** when it is resolved.
*   Daily **Egg**s, if you hold the Supporter entitlement — including the one-time 18+ consent prompt.
*   **Occasional donation or Discord Store messages**, roughly once per 20 **Egg**s you create.

The first two categories are service messages tied to an action you took. The third is promotional: you can **opt out at any time** by emailing [flamey@hexa.blue](mailto:flamey@hexa.blue) or messaging [actuallyflamey](https://discord.com/users/450678229192278036), and we will stop sending them. You can also block the Bot in Discord to stop all DMs.

## 7. Controls You Have

*   **Hide your server's invite link:** `/config privacy public:False` (requires Manage Server). The invite button will stop appearing on **Egg**s from your server.
*   **Hide your username from leaderboards:** `/config privacy public:False` run as a personal command. Your display name still appears.
*   **Restrict ratings:** `/config allowed-ratings` and `/config channel-rating` control which content ratings can be created and where they can be retrieved.
*   Block specific **Egg**s in your server with `/filter`.
*   **Decline or withdraw explicit-content consent:** the Supporter daily-**Egg** prompt has a "No" option, and you can withdraw consent at any time by contacting us. Withdrawing stops explicit **Egg**s appearing in your daily DMs.
*   **Opt out of promotional DMs:** see Section 6.
*   **Object to processing** on legitimate-interest grounds: see Section 8.
*   **Don't use the Bot.** Uninstalling it or blocking it stops all collection going forward.

## 8. How Long We Keep It, and Your Rights

### 8.1 Retention — why it is open-ended

We keep data for as long as it serves the purpose it was collected for, which for most records is indefinite. That is not laziness; here is the justification required by **Art. 5(1)(e)**:

*   Your **Egg**s are stored until you delete them (via `/delete`), until a moderator removes them, or until you request deletion. Deleting an **Egg** also deletes its stored media file. **Egg**s must persist for as long as they are shareable, because their whole point is being retrievable later on other servers.
*   **Your user record** (ID, language, flags, collections) is kept so that **Egg**s remain attributable and searchable, and so leaderboards and collections stay consistent.
*   **Battles and votes** are kept as battle history and leaderboard data.
*   **Reports** are kept as a moderation record, so we can show why a decision was made.
*   **Server configuration is deleted automatically** the moment the Bot leaves your server — the invite link, log channel, ratings, filter list, and description are erased at that point. *(Note: **Egg**s created in that server are not automatically deleted with it.)*

If you stop using the Bot, your data is not erased automatically, because the records above are still needed for the reasons listed. You can end that at any time by exercising your right to erasure below.

### 8.2 Your rights

As an EU/EEA data subject you have, under GDPR Chapters III–VII:

*   **Right of access (Art. 15)** — find out what we hold about you. Email [flamey@hexa.blue](mailto:flamey@hexa.blue) and we will send your user record, your **Egg**s, your votes, and your reports in a readable format, **within one month**.
*   **Right to rectification (Art. 16)** — correct inaccurate data, or update your language/privacy settings yourself via `/config`.
*   **Right to erasure / "right to be forgotten" (Art. 17)** — ask us to delete your user record, your **Egg**s, and your activity data. Email us and we will do it, barring any legal obligation that requires us to keep a specific record (e.g. a moderation record we must retain to justify a ban).
*   **Right to restriction of processing (Art. 18)** — ask us to pause processing while a dispute is resolved.
*   **Right to data portability (Art. 20)** — receive your data in a structured, machine-readable format (we will provide JSON).
*   **Right to object (Art. 21)** — object at any time, on grounds relating to your particular situation, to processing based on legitimate interest, including promotional DMs. We must then stop unless we demonstrate compelling legitimate grounds.
*   **Right to withdraw consent (Art. 7(3))** — withdraw any consent at any time, without affecting prior lawful processing. This applies to the explicit-content DM flag.
*   **Right not to be subject to automated decisions (Art. 22)** — see Section 8.3.
*   **Right to lodge a complaint (Art. 77)** — you may complain to your national supervisory authority. As we are established in the EU/EEA, you can also contact the authority in your member state of residence or habitual appeal. A list of EU authorities is available at [edpb.europa.eu](https://www.edpb.europa.eu/about-edpb/about-edpb/members_en).

To exercise any of these, email [flamey@hexa.blue](mailto:flamey@hexa.blue). We respond without undue delay and **within one month**, extendable by two months for complex requests (with notice under Art. 12(3)).

### 8.3 Automated decision-making

One decision is made with significant automated assistance: if the safety scan matches your upload against known child sexual abuse material, your **Egg** is **automatically deleted** and you are **automatically banned** from creating **Egg**s, without a human reviewing the upload first.

This is not a decision made purely by machine with no recourse. **Human review is always available:** moderators and the developer can inspect a ban and reverse it (`/dev unban`), and every user report is reviewed by a human before any action. You may request human review of a ban through any contact channel in Section 12, and you may contest the decision and express your point of view.

No other automated decisions with legal or similarly significant effects are made about you.

## 9. Children's Data

The Bot requires you to meet Discord's minimum age of **13**, which is also the floor set by the GDPR for information-society services. The digital-consent age in your member state may be **higher (up to 16)**. If you are below your country's age of digital consent, your use of the Bot should be authorised by your parent or guardian; if it was not, or if you are a parent/guardian of such a user, contact us and we will delete that data. See Section 2 of the Terms of Service for the age rule.

## 10. Security

We take reasonable technical and organisational measures appropriate to the risk (**Art. 32**):

*   The database and stored media live on private infrastructure and are **not** part of the public source repository; credentials are held in environment variables excluded from version control.
*   Access is limited to the developers.
*   Media is stored in quarantine, invisible to other users, until the safety scan clears, so prohibited material is never distributed.

In the event of a personal data breach likely to result in a risk to your rights, we will notify the competent supervisory authority within 72 hours (**Art. 33**) and, where the risk is high, notify you without undue delay (**Art. 34**).

## 11. Open Source and Database

The Bot's source code is public under the [GPL-3.0 license](https://github.com/WeAreHexaBlue/ServerEggs). **The code being public does not make the database public** — the PostgreSQL database and the stored media files are private and secured by the developers. Self-hosting the code gives you your own, separate database.

## 12. Contact Us

For privacy questions, data-subject rights requests, deletion requests, or anything else in this policy:

*   **Email:** [flamey@hexa.blue](mailto:flamey@hexa.blue) — preferred for legal and rights requests, since it leaves a record.
*   **Discord:** [actuallyflamey](https://discord.com/users/450678229192278036)
*   **GitHub:** https://github.com/WeAreHexaBlue/ServerEggs

## 13. Changes to This Policy

We may update this policy to reflect changes in the code. The "Last Updated" date at the top will change when we do. Material changes will be announced in our support server or through the Bot where practical, and where a change affects the legal basis for an existing purpose we will re-confirm consent or rely on another valid basis. Continued use after a change means you accept the updated policy.

---

See also: [**Terms of Service**](TERMS.md) · [Source Code (GPL-3.0)](https://github.com/WeAreHexaBlue/ServerEggs)
