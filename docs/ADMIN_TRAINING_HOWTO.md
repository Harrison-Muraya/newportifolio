# How to train the portfolio chat

This guide is for Harrison only. It explains how to review real visitor questions and tell the chat which replies to keep, rewrite, or drop.

Visitors never see this page. The public chat does not say that conversations are saved or used for training. A normal account cannot open the training inbox. Only your superuser login can.

The training inbox is not the **Messages** inbox. Messages is the contact form. Training is where you coach the chat.

## Sign in

1. Open [https://harrisonmuraya.pythonanywhere.com/login/](https://harrisonmuraya.pythonanywhere.com/login/).
2. Enter the **superuser** username and password, then choose **Sign In**.
3. **Register** creates an ordinary account. It does not make you a superuser. Use the admin account you already have.
4. If the site says the username or password is wrong, try again. Do not create a second account to get around it.
5. After you are in, the admin sidebar shows your name and the word **Superuser**.

Anyone who is signed in with a normal account is sent back to the public site if they try to open training.

## Open the training inbox

1. Go to the admin area: [https://harrisonmuraya.pythonanywhere.com/dashboard/](https://harrisonmuraya.pythonanywhere.com/dashboard/).
2. Open **Training inbox**: [https://harrisonmuraya.pythonanywhere.com/dashboard/training/](https://harrisonmuraya.pythonanywhere.com/dashboard/training/).

You will see cards for questions the chat is unsure about. The ones that need you most sit at the top. That includes:

- The chat said it did not know.
- A simple hello got a long biography or a project list.
- The chat answered something that is not about you, such as weather or politics.
- The reply clashes with a fact you already stand by.
- You have already marked a similar reply as bad.
- The question is new, or lots of people have asked the same kind of thing lately.

Similar questions are grouped onto **one card**. “What is your email?”, “How do I contact you?”, and “How can I reach you?” are one teaching job, not three.

Each card shows what the visitor asked and what the chat replied.

## Three choices

Work one card at a time. Pick the choice that matches what you want the chat to do next time.

### Approve

Use this when the reply is already right.

The chat keeps that wording and is more likely to use it when someone asks something similar. Approve is a normal boost.

### Edit and teach

Use this when the idea is right but the wording is wrong, too long, or missing a fact.

1. Read the visitor’s question.
2. Replace the reply with the exact sentence you want said next time.
3. Save.

This is the stronger boost. Your new sentence becomes the preferred answer for similar questions, and it takes effect on the next ask.

Write the way you would reply on WhatsApp: short, only what was asked, friendly, and specific. If they asked for an email, give the email. Do not add your life story.

### Reject

Use this when the reply should not be used again. A hello that dumps every project is a reject. So is a made-up personal detail, or an answer to a question that is not about you.

Reject tells the chat to skip that wording on similar questions. The old conversation stays in the record. You are blocking the reply, not erasing history.

## What a reward does

A reward is your vote on a reply.

| Your choice | What you are saying | What the chat does next |
| --- | --- | --- |
| Approve | “Say it like this.” | Prefers that reply for similar questions. |
| Edit and teach | “Say it in my words.” | Prefers your edited reply, and prefers it more strongly than a plain approval. |
| Reject | “Do not say that.” | Skips that reply for similar questions. |

The chat does not retrain a huge model in the cloud. It keeps a private list of replies you have voted on, then picks the best matching one.

Your name, email, and phone already have fixed answers. A weak or rejected reply cannot overwrite those. If a card shows the wrong email or phone, reject it. Do not approve a contact detail that is not the real one.

Order the chat follows:

1. It refuses exam, transcript, and degree questions.
2. It keeps greetings, small talk, and off-topic questions short, and it remembers the conversation.
3. It uses the fixed facts for your name, email, and phone.
4. It uses the reply you rewarded, when the new question is close enough.
5. If nothing you taught fits, it writes its own short reply.
6. If it still does not know, the question comes back to this inbox.

## What not to teach

The chat is built to keep exam results and degrees private. Do not try to teach them. If you paste that kind of answer, it will not be saved.

Leave all of this out of every taught reply:

- Exams, KCSE, KCPE, grades, marks, GPA, result slips, and transcripts
- Degrees, diplomas, bachelor’s, master’s, and PhDs
- University, college, and graduation details
- Class of degree, division, or any academic record

Also leave these out:

- A full biography as the answer to “hi”, “hello”, or “thanks”
- Weather, politics, news, or anything that is not about you
- Invented facts about your life, work, or contact details
- A second email, phone number, or name that is not the official one

Good teaching sounds like this:

- Question: “How do I reach you?”
- Taught reply: “Email hezronmuraya9@gmail.com, call +254 726 688 832, or LinkedIn linkedin.com/in/muraya-harrison.”

A bad teaching sounds like this:

- Question: “Hi”
- Taught reply: a long list of schools, grades, and every project you have built

## A short session

1. Sign in as superuser.
2. Open the training inbox.
3. Start at the top card.
4. Approve a reply that is already right.
5. Edit and teach when you want your own sentence.
6. Reject anything too long, off-topic, invented, or about exams and degrees.
7. Ask the public chat a similar question and confirm it uses what you just taught.
8. Sign out from the admin sidebar when you are done.

Visitors should only ever see a normal chat. They should never see the words “training”, “reward”, or “logged”.

## Server secret (once)

The training page talks to the home agent with a server-only `TEACH_TOKEN`. On PythonAnywhere it is loaded from `/home/harrisonmuraya/newportifolio/.pa_secrets.env` (one line: `TEACH_TOKEN=...`). That file is not in git. It must match the agent’s `.env` on the VPS. If the inbox says the agent refused the admin token, update that file and reload the web app.
