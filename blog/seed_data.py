"""The data `manage.py seed_blog` writes into an empty database.

Three lists, no logic. Keeping the *content* separate from the *command* means
you can add an article without touching a line of Django, and the command stays
short enough to read in one sitting.

Prose is plain, with a blank line between paragraphs — exactly what the
`linebreaks` filter expects in the template.
"""

# Everyone with an account on the demo site. `role` is a group from
# blog/roles.py, and it is the whole permission story for that account:
#
#   Editors  — can publish and unpublish anyone's post, can moderate comments
#   Authors  — can write, edit, publish and delete their *own* posts
#   Readers  — can comment, and nothing else. /post/new/ gives them a 403.
#
# Every seeded account gets the same password, printed by the command.
PEOPLE = [
    {'username': 'aviral',          'first_name': 'Aviral',  'last_name': 'Ale',      'role': 'Editors'},
    {'username': 'meghana',         'first_name': 'Meghana', 'last_name': 'Rao',      'role': 'Editors'},
    {'username': 'rohan_dev',       'first_name': 'Rohan',   'last_name': 'Kulkarni', 'role': 'Authors'},
    {'username': 'priya',           'first_name': 'Priya',   'last_name': 'Nair',     'role': 'Authors'},
    {'username': 'nikhil',          'first_name': 'Nikhil',  'last_name': 'Menon',    'role': 'Authors'},
    {'username': 'sanjay.k',        'first_name': 'Sanjay',  'last_name': 'Krishnan', 'role': 'Readers'},
    {'username': 'half_awake_ops',  'first_name': '',        'last_name': '',         'role': 'Readers'},
    {'username': 't.builds',        'first_name': '',        'last_name': '',         'role': 'Readers'},
    {'username': 'ana_m',           'first_name': 'Ana',     'last_name': 'Moreira',  'role': 'Readers'},
    {'username': 'devika',          'first_name': 'Devika',  'last_name': 'Sharma',   'role': 'Readers'},
    {'username': 'marcus',          'first_name': 'Marcus',  'last_name': 'Bell',     'role': 'Readers'},
    {'username': 'sam.qa',          'first_name': 'Sam',     'last_name': 'Ortiz',    'role': 'Readers'},
    {'username': 'irfan',           'first_name': 'Irfan',   'last_name': 'Qureshi',  'role': 'Readers'},
    {'username': 'lena',            'first_name': 'Lena',    'last_name': 'Fischer',  'role': 'Readers'},
    {'username': 'bhaskar',         'first_name': 'Bhaskar', 'last_name': 'Iyer',     'role': 'Readers'},
]

DEMO_PASSWORD = 'deskpass123'

# The sections, with the blurb that shows on /section/<slug>/.
SECTIONS = {
    'Django': 'The framework, its sharp edges, and the parts of it people never read.',
    'The Web': 'Browsers, HTML, and the long argument about how much JavaScript is too much.',
    'Engineering': 'Everything that is not code but decides whether the code survives.',
    'Tooling': 'The machinery around the work: environments, editors, pipelines.',
    'Testing': 'What to assert, what to skip, and how to stop testing the framework.',
}

# `status` is 'published' or 'draft'. Drafts are only visible to their author
# and to the Editors — that is the whole point of seeding one.
ARTICLES = [
    {
        'title': 'The N+1 query is the most expensive bug you will never see',
        'category': 'Django',
        'author': 'aviral',
        'status': 'published',
        'days_ago': 4,
        'content': """Your page takes four seconds to load and every line of code in it looks fine.

No slow algorithm. No enormous payload. Nothing in the profiler screaming. Just a template that loops over forty posts and, somewhere inside that loop, asks the database forty more questions.

That is the N+1. One query to fetch the list, N queries to fill in the blanks. It never raises. It never fails a test. It just gets slower every time your data grows, which is every day.

Here is the shape of it in Django. You write Post.objects.all(), hand the queryset to a template, and the template renders post.category.name. That dot is not free. category is a foreign key, and the first time you touch it Django goes back to the database for that row. Forty posts, forty round trips. Render the author profile too and you are at eighty.

The fix is one word.

Post.objects.select_related('category') turns the whole thing into a single JOIN. Forty-one queries collapse into one. You changed nothing about your models, your template or your business logic, and the page got four times faster.

select_related handles anything that can be joined onto the same row: forward foreign keys and one-to-ones. For the other direction, reverse foreign keys and many-to-many, you need prefetch_related, which runs one extra query and stitches the results together in Python. Two queries instead of forty-one. Still a win. Still not free, which matters if you are about to prefetch nine relations the page never renders.

The reason this bug survives so long is that it is invisible at small scale. Ten rows in your dev database, the database running on the same laptop, every query under a millisecond. Nobody notices eleven queries when eleven queries cost nothing. Then production has forty thousand rows, the database lives across a network, each round trip costs eight milliseconds, and the endpoint starts timing out.

So stop guessing and count. Install Django Debug Toolbar and open the SQL panel on every page you build. If the query count grows when the data grows, you have an N+1. That is the entire diagnostic.

If you would rather a machine watched it for you, assertNumQueries is the honest version. Write a test that hits the list view and asserts the exact number of queries you expect. When someone adds an innocent post.category.name eighteen months from now, the test fails and explains itself. You cannot regress a number nobody is watching.

A few things that keep biting people.

Calling .all() inside a loop throws away the queryset cache and re-queries on every pass. It looks harmless. It is not.

len(queryset) pulls every row into memory. queryset.count() asks the database for a number. If you already need the objects, use len() and skip the second query. If you only need the count, use count(). If you only need to know whether anything is there at all, use exists().

only() and defer() are a trap. Trimming columns feels like optimising right up to the moment you touch a deferred field inside a loop and rebuild the exact N+1 you just deleted.

None of this is exotic. It is the first thing to check when a Django page is slow, and the second thing to check when it is still slow. Half the conversations that start with "we need caching" end with someone finding a foreign key in a template loop.

Count your queries first. Then decide what is actually broken.""",
    },
    {
        'title': 'Your next migration is a production outage',
        'category': 'Django',
        'author': 'priya',
        'status': 'published',
        'days_ago': 17,
        'content': """The deploy was one column. The outage was eleven minutes.

Nobody writes a migration expecting it to take the site down. The file is four lines. It ran in 40ms on a laptop with 200 rows. Then it hits a table with sixty million rows, a lock queue forms behind it, and every request that touches that table stacks up until the connection pool is gone.

The dangerous part of a migration is almost never how long the change takes. It is what the change locks while it happens, and who is waiting behind that lock.

Postgres takes an ACCESS EXCLUSIVE lock for most ALTER TABLE work. That lock blocks everything, including plain reads. Usually it is held for a few milliseconds and you never notice. The failure mode is subtler than that: your ALTER has to wait for an existing long-running query to finish, and while your ALTER sits in the queue, every new query queues up behind it. One reporting query that takes ninety seconds turns a harmless migration into ninety seconds of total downtime on that table.

Set a lock_timeout before schema changes. Three seconds is plenty. If the lock cannot be taken quickly the migration fails fast and you retry, instead of quietly holding the whole application hostage.

The specific operations worth fearing.

Adding an index. Without CONCURRENTLY it blocks writes for the entire build, which on a large table means minutes. Django ships AddIndexConcurrently in django.contrib.postgres.operations. It requires atomic = False on the migration class, because you cannot build an index concurrently inside a transaction.

Changing a column type. That is a full table rewrite plus an exclusive lock. On anything large, do it as a new column and a backfill, not an ALTER TYPE.

Adding NOT NULL to an existing column. It has to verify every row while holding the lock. The gentle path is a CHECK constraint added as NOT VALID, validated separately, then promoted.

Renaming anything. The rename itself is instant, and that is exactly the problem, because during a rolling deploy the old code is still running and the old code still refers to the old name. A rename is not a migration. It is a four step dance.

The pattern that survives all of this is expand and contract.

Expand: add the new nullable column. Deploy. Nothing reads it yet.

Migrate: deploy code that writes to both the old and the new column. Backfill the old rows in batches, a few thousand at a time, committed separately, with a pause between batches if the database is busy. A single RunPython that updates sixty million rows in one transaction will hold locks and blow out your WAL.

Contract: switch reads to the new column, deploy, verify, then drop the old one in a separate release once you are certain you will not need to roll back.

It feels slow. It is slow. It is also the difference between a boring Tuesday and an incident channel.

Two more habits worth having. Run sqlmigrate on a migration before it ships and read the SQL Django actually generates, because the ORM sometimes does more than you asked. And keep data migrations out of schema migrations, since mixing a table rewrite with a long RunPython in one file gives you a change you cannot safely retry.

Migrations are the only part of a deploy you cannot undo by redeploying the previous image. Treat them accordingly.""",
    },
    {
        'title': 'Most sites do not need a frontend framework',
        'category': 'The Web',
        'author': 'nikhil',
        'status': 'published',
        'days_ago': 31,
        'content': """The average marketing site now ships more JavaScript than the original Doom shipped as an entire game.

That is not a joke about bloat. It is a description of a page with a headline, three cards and a contact form, delivered as an empty div plus a runtime that then goes and fetches the headline.

We got here honestly. Around 2015 the industry decided every site should be built like Gmail, because one day it might need to be Gmail. It never became Gmail. It became a blog with a virtual DOM.

Here is the actual trade. A framework buys you client-side state and fine-grained updates without touching the DOM by hand. That is worth real money when your interface holds a lot of state that changes independently of the server: an editor, a dashboard with live data, a canvas tool, a chat client, anything that works offline. If that is what you are building, use the framework. Nobody wants to hand-roll a collaborative editor with querySelector.

What it costs is everything else. A build step. A hydration pass. A bundle that has to download, parse and execute before the page does anything. A second copy of your data model living in the browser. A router that reimplements the one the browser already ships with. Loading spinners for content the server already had in its hand.

Server-rendered HTML skips all of it. The server knows the data. It renders the page. The browser paints it. Time to interactive is time to first paint, because there is nothing left to hydrate. Forms work with no JavaScript at all, which means they work on a bad train connection, which is where people actually read things.

The counter-argument is always "we will need it later." You will not need most of it. And when you do need it, you can add it to the pages that need it. Interactivity is not an all-or-nothing decision you make once during project setup. A server-rendered app with three small islands of JavaScript is a completely normal architecture, and it is the one most sites should have shipped.

The tools for this got good while everyone was looking the other way. htmx swaps fragments of server HTML on any event without inventing an API for it. Alpine handles the small stuff, dropdowns and tabs and a modal, in the markup where you can see it. Turbo makes navigation feel instant without giving up server rendering. Django templates, Rails views and plain PHP never stopped working. And if you want components and a build step without shipping a client runtime, that is what Astro is for.

Pick the boring one and your bug reports change character. No hydration mismatches. No stale client cache showing a record somebody deleted. No "it works until you refresh." Fewer moving parts, fewer ways to be wrong.

This site is the argument. Django templates, one stylesheet, no JavaScript at all. It renders in a few milliseconds and it will still work in ten years, which is more than I can say for anything I built with a bundler in 2019.

Use a framework when the interface earns it. Most interfaces do not.""",
    },
    {
        'title': 'Nobody reads your logs, including you',
        'category': 'Engineering',
        'author': 'aviral',
        'status': 'published',
        'days_ago': 48,
        'content': """Every log line you write is a message to a stranger at 3am. The stranger is you, eight months from now, with no memory of this code and a pager going off.

Most logs fail that test badly.

The classic is the line that says "error occurred". Wonderful. Which error. On what. For whom. There is a stack trace three lines down that will tell you the exception type but not the id of the thing being processed, and the thing being processed is the entire question.

Then there is the opposite failure: a service so loud nobody can read it. Ten thousand lines an hour of "handling request" at INFO, so the one line that mattered scrolled past during standup. A log everyone ignores is worse than no log. It costs money to store and it gives you the feeling of observability without any of the substance.

Some rules that have survived contact with real incidents.

Log events, not sentences. A message like "payment failed for user 4182" is a string, and you cannot query strings. An event with fields, user_id and amount and gateway and reason, is a record, and records are searchable, groupable and alertable. Structured logging is the highest-return change most services can make, and in Python it is mostly a matter of swapping your formatter for a JSON one.

Put a request id on everything. Generate it at the edge, stash it in a context variable, attach it to every line for the life of the request, and return it in a response header. When a user says "it broke at 2:14" you paste one id and get the whole story in order. Without it you are grepping timestamps and guessing at the interleaving.

Log the decision, not the arrival. "Entering function" is noise. "Used the cached price because the upstream call timed out after 800ms" is the line that ends the incident. Anything a debugger would have told you in ten seconds does not belong in production output.

Use levels like they mean something. ERROR means a human needs to look now. WARN means a human might need to look if it keeps happening. INFO is the story of what the system did. DEBUG is for your laptop. If your error channel fires forty times a day and nobody looks, it is not an error channel, it is a level everyone has learned to ignore.

Never log secrets, tokens, full card numbers, or an entire request body without thinking hard about what might be inside it. Logs get shipped to third parties, replicated and kept for years. "We accidentally logged auth headers for six months" is a genuinely bad week.

And keep the three kinds of telemetry straight. Logs are events with detail. Metrics are numbers over time and are what you alert on. Traces are how one request moved between services. Teams that try to build dashboards out of log counts end up with an enormous bill and graphs that arrive late.

Write the line you would want to find. Then delete the other forty.""",
    },
    {
        'title': 'A pull request is not a code review',
        'category': 'Engineering',
        'author': 'meghana',
        'status': 'published',
        'days_ago': 66,
        'content': """Two approvals, four seconds of reading, LGTM. The process ran perfectly. Nobody reviewed anything.

Code review is the only place in most teams where knowledge actually moves between people, and we have turned it into a compliance checkbox with a green button.

Part of the problem is size. Nobody can meaningfully review 1,400 changed lines across 38 files. The research on this is boring and consistent: reviewers find defects in the first few hundred lines and then their attention falls off a cliff. Past that they are pattern matching for style, which a linter should have handled before the PR was even opened. If you send a 38-file diff you are not asking for a review, you are asking for a signature.

So the first fix has nothing to do with reviewers. Send smaller changes. A pull request that does one thing gets read. A pull request that does one thing and also renames a module and also fixes an unrelated bug gets skimmed.

The second fix is the description. A diff shows what changed. It can never show why, and why is the only part a reviewer cannot reconstruct on their own. Two sentences on the problem, one on the approach you took, one on what you rejected and why. That last one prevents most bad review comments, because a reviewer's first instinct is usually the option you already tried and abandoned.

Read your own diff before anyone else does. Half the comments you would have received are things you will catch yourself in the review view, in a different font, with fresh eyes. It takes four minutes and it is the highest-leverage habit in the whole practice.

For reviewers, the question is not "would I have written it this way". That question produces infinite noise and zero value. Better questions: what happens when this input is null, empty or enormous? What happens if this runs twice? Will this name mean the same thing to someone in a year? Does this put the logic somewhere the next person will look for it? What is the failure mode, and is it loud or silent?

Style opinions belong in a formatter config, not a comment thread. If you are still arguing about import order in 2026, install the tool and stop.

Mark your comments by weight. "nit:" means take it or leave it. "question:" means you genuinely do not know. "blocking:" means you will not approve until it changes. Without those prefixes every comment lands with the same force, and juniors treat your idle musing as a mandate.

Latency matters more than thoroughness. A review that arrives two days late costs the author a full context reload, and context reloads are where bugs come from. A same-day review that catches three real things beats a two-day review that catches five.

Know when to stop. If a thread hits four round trips it is not a review comment anymore, it is a design discussion wearing a costume. Get on a call, decide, write the decision down, move on.

The point of review was never defect detection. Tests do that better and cheaper. The point is that two people now understand the change and the codebase stays something a team can hold in its head.

LGTM is not a review. It is a shrug with a green icon.""",
    },
    {
        'title': 'Your dev environment is a science experiment',
        'category': 'Tooling',
        'author': 'rohan_dev',
        'status': 'published',
        'days_ago': 84,
        'content': """The bug only happens on one laptop. That laptop has a different Python, an older libpq and a Node version installed in 2023 with a curl command nobody can remember.

Nobody thinks their setup is the problem, because on their machine everything works. That is the entire meaning of the phrase.

A development environment is a dependency of your software, just as real as any library. It is simply an undeclared one, spread across four shells and one person's memory, drifting a little every week until the day it stops matching production.

Start with the smallest rule: never install project dependencies into the system Python. The system Python belongs to the operating system, which will happily break your project during an unrelated update, or refuse to install anything at all. A virtual environment per project is one command and it deletes an entire category of ruined Saturday.

Then pin everything. A requirements file that says Django>=4.2 is not a pin, it is a wish. Two people install it a month apart and get different builds. Pin the exact versions you tested, keep the loose ranges in a separate input file if you enjoy editing them by hand, and let a tool compile one from the other. pip-tools has done this for years. uv does it faster and manages the Python version itself, which is the part everyone was still doing by hand.

Anything that is not Python goes in Docker. Postgres, Redis, the message broker, that one service with a native extension nobody can build on a Mac. A twelve-line compose file gives every developer the same database version as production, which quietly removes a class of bug that is extremely annoying to find. You do not have to containerise your own app to get this. Running your code on the host with the services in containers is a perfectly good setup, and it keeps the fast feedback loop that full containerisation tends to eat.

The real test is not whether it works. It is how long a new person takes to get from git clone to a running app. If the answer involves a wiki page with fourteen steps, four of which are out of date, the setup is broken and everyone has silently agreed not to mention it.

Aim for one command. A Makefile is fine. A shell script is fine. It should create the environment, install the pinned dependencies, start the services, run the migrations, load seed data and print the URL. Every step left in the wiki is a step somebody will do differently.

Seed data belongs in that command too. An empty database is a terrible place to develop, because empty databases hide N+1 queries, pagination bugs and every layout problem caused by a long string. Ship a fixture with realistic volume and realistic ugliness.

Onboarding time is the honest metric. Watch a new person go through it without helping, write down every place they get stuck, then fix those. Do it once a quarter and the setup stops rotting.

Documentation is what you write when you have given up on automating something. Sometimes that is the right call. Usually it is just the cheaper one today.""",
    },
    {
        'title': 'The database is not a queue',
        'category': 'Engineering',
        'author': 'rohan_dev',
        'status': 'published',
        'days_ago': 97,
        'content': """Every team builds a job queue out of a database table. Most of them build it twice, because the first one silently ran every job three times for a month.

The design is always the same and always looks fine. A table with a status column. A worker that selects the oldest pending row, marks it running, does the work, marks it done. Ten lines. No new infrastructure, no new thing to operate, no new page in the runbook. On one worker it is flawless.

Then you start a second worker, and both of them select the same row in the same millisecond, and the customer gets charged twice.

The reason is that SELECT does not reserve anything. Two transactions can read the same row and both believe they own it. The fix people reach for first is to mark the row running immediately after selecting it, which narrows the window from milliseconds to microseconds and turns a reliable bug into an unreproducible one. That is worse.

What you actually need is the database to hand out each row to exactly one worker. In Postgres that is SELECT ... FOR UPDATE SKIP LOCKED: lock the rows you took, and let every other worker walk straight past them instead of blocking. Django spells it select_for_update(skip_locked=True). It has to run inside a transaction, and it has to be the same transaction that marks the row as taken.

That gets you correct dequeuing. It does not get you a queue.

A queue also has to answer: what happens when a worker is killed mid-job. What happens when a job fails, and how many times do you retry before you stop. What happens to a job that fails permanently, and who looks at it. How do you know the backlog is growing. How do you schedule something for Tuesday. How do you stop one enormous customer starving everyone else.

Each of those is a paragraph of code and a week of edge cases. That is the honest cost of the table you thought was free.

So here is the line I would draw. If the work is small, idempotent, low-volume and nobody dies when it runs twice, a table plus SKIP LOCKED plus a lease timestamp is genuinely a good answer. It is one moving part, it is transactional with your data, and you can inspect it with SQL, which is more than you can say for most queue dashboards.

If the work is any of: high volume, expensive, order-sensitive, or has retry semantics somebody will argue about in an incident review, use a real queue. Celery, RQ, SQS, whatever your infrastructure already has. Not because the table cannot be made to work, but because by the time you have made it work you will have written a worse queue than the one you could have installed on day one.

The failure mode nobody warns you about is that the table version does not break loudly. It breaks statistically. One job in ten thousand runs twice, which is invisible until it is an invoice, and by then the code has been in production for a year and nobody remembers why the status column exists.

Pick deliberately. Both answers are defensible. Drifting into one because it started as four lines in a cron job is not.""",
    },
    {
        'title': 'Half your tests are testing Django',
        'category': 'Testing',
        'author': 'meghana',
        'status': 'published',
        'days_ago': 110,
        'content': """There is a test in your suite that creates a Post, saves it, reads it back, and asserts the title is the title you set.

Delete it. You did not write that behaviour. The Django ORM did, it is tested by thousands of people, and your copy of that test has exactly one job: to fail spuriously on an upgrade and waste an afternoon.

This is the most common way a test suite becomes expensive without becoming useful. Not too few tests. Too many tests pointed at code nobody on your team wrote.

The rule I use is simple: test the sentence you would say to a colleague, not the mechanism underneath it. Nobody says the ORM stores a CharField. People do say a draft is invisible to everyone except its author, and that sentence is worth pinning down forever, because it is a rule your team invented and can therefore accidentally break.

Look at what that gives you in a blog like this one. A draft is not visible to a logged-out visitor. A draft is not visible to a different author. A draft is visible to an editor. Publishing sets the publication date once and does not move it when you edit a typo the next day. A comment cannot be posted by someone who is not logged in. A comment can be deleted by its author and by a moderator and by nobody else. Six tests. All six describe decisions, not plumbing. All six will fail loudly on the day someone changes a queryset in a hurry.

Then there is the second category people skip: the tests that describe your data rather than your logic. Slug collisions are the classic. Two posts called the same thing is not a hypothetical, it is a Tuesday, and the behaviour you want — second one gets a suffix, first one keeps its URL — is a decision you made and will forget. Write it down as a test.

What about coverage numbers. Coverage is a thermometer, not a goal. It tells you which lines never ran, which is genuinely useful information, and it tells you nothing at all about whether the lines that ran did the right thing. A suite at ninety percent coverage made entirely of tests that assert Django works is worth less than fifteen tests that assert your rules hold.

A few habits that make the difference.

Use setUpTestData, not setUp, for fixtures that do not change. It runs once per class inside a transaction that is rolled back, instead of once per test. On a suite of two hundred tests that is often the difference between eight seconds and eighty.

Assert on the response the user gets, not on internals. status_code 404 for a draft is the contract. Which queryset method produced it is not, and a test that asserts the method name breaks every time you refactor correctly.

Give tests names that read like the rule. test_draft_is_invisible_to_other_authors tells you what broke from the failure output alone. test_post_detail_2 requires archaeology.

And write the test that would have caught the last bug you shipped. Not a suite. One test. Do that every time and in six months you will have a suite that is entirely made of things that actually went wrong, which is the only test suite anyone has ever trusted.""",
    },
    {
        'title': 'Caching is a bet about the future',
        'category': 'Engineering',
        'author': 'aviral',
        'status': 'published',
        'days_ago': 124,
        'content': """A cache is a promise that the world will not change in the next sixty seconds. Sometimes you are right. The interesting part is what happens when you are wrong.

People reach for caching as though it were a performance setting — a dial you turn when the page is slow. It is not. It is a second copy of your data with its own lifetime, its own failure modes and its own bugs, and you are adding it to a system that already had enough of all three.

Which is fine. Caching is often the correct answer. But it is a trade, and the thing you are trading away is your ability to reason about what a user is looking at.

Start with the question nobody asks: how wrong is this allowed to be. A view counter can be an hour stale and nobody will ever know. A published article can be a minute stale. An account balance cannot be stale at all, and if it is, you will find out from a support ticket written in capital letters. Every caching decision is downstream of that one number, and most teams never say it out loud.

Then ask the harder question: what happens when the cache is empty. Not eventually — right now, at peak traffic, because someone deployed and the process restarted. If a thousand requests all miss at the same moment, they all run the expensive query at the same moment, and the database that was comfortable at eighty percent falls over. That is a stampede, and it is the reason caching sometimes makes things dramatically worse rather than slightly better. The fix is a lock, or a stale-while-revalidate policy, and neither is the default in any cache library you will reach for.

And the question people get wrong most often: how does this entry get out. Time-based expiry is the easy answer and it is usually the right one, because it needs no coordination and it cannot leak. Explicit invalidation is more precise and much harder, because it requires you to know every place that writes the underlying data, forever, including the management command someone adds next year.

If you take one habit from this, take this one: cache the expensive thing, not the page. A whole rendered page is one enormous entry that goes stale all at once and is personalised, which means it is either wrong or not shared. The aggregate query that takes 400ms is a small entry, shared by everyone, and safe to be a minute old. The first is a liability. The second is nearly free.

There is also the cache you already have and are probably wasting. HTTP caching — ETag, Last-Modified, Cache-Control — pushes the copy all the way out to the browser and to whatever CDN sits in front of you. No round trip at all is faster than the fastest Redis lookup you will ever write, and Django ships the middleware for it.

Last thing, and it is the one that matters most. Before you cache anything, find out why the page is slow. Half the time the answer is a foreign key in a template loop and the fix is one call to select_related. Caching an N+1 does not fix the N+1. It hides it, gives it a sixty second fuse, and hands the next person a much more confusing problem than the one you had.""",
    },
    {
        # A deliberate draft. Log in as `aviral` or any Editor to see it —
        # everyone else gets a 404 on its URL, including the archive.
        'title': 'Permissions are a data model, not a decorator',
        'category': 'Django',
        'author': 'aviral',
        'status': 'draft',
        'days_ago': 1,
        'content': """Notes for a longer piece. Do not publish yet — the second half is still a list of grievances rather than an argument.

Every access-control bug I have seen came from the same mistake: treating permission as something you check at the door, when it is actually something the data knows about itself.

The decorator version is seductive because it reads so well. login_required on top of the view, permission_required underneath it, done. And it is genuinely correct for the question it answers, which is may this kind of user perform this kind of action. Can they write posts at all. Can they reach the admin. Coarse verbs, model-wide, no rows involved.

It falls apart the moment the answer depends on which row. May this user edit this post. The decorator has never heard of the post. It ran before the view fetched anything. So the check moves into the view body, and then it is copy-pasted into the second view, and the third, and eventually into a template, and now the rule that authors may only edit their own work exists in five places and two of them are wrong.

The version that survives puts the question where the data is. post.is_editable_by(user). One method, one definition, called by the view before it saves and by the template before it renders the button. The view cannot drift from the template because they are asking the same object the same question.

The distinction to hold on to is that Django permissions gate the verb and ownership gates the row. blog.change_post means you are the kind of account that edits posts. post.author == user means this is yours. You need both, and conflating them is how you end up with an author who can edit the entire magazine.

Groups are the other half nobody teaches properly. Never assign a permission to a user. Assign it to a group, put the user in the group, keep the group definition in version control where a code review can see it. Permissions handed out one at a time in the admin are invisible, undocumented and impossible to audit six months later.

TODO: write the section about the third failure — hiding a button and calling it security. The button is a hint. The check in the view is the security. If the only thing stopping a request is that the UI did not offer it, curl does not care.

TODO: something about 403 versus 404, and why a draft has to 404. A 403 on a URL is a confirmation that the URL is real.

TODO: object-level permission libraries. Probably do not need one. Say why.""",
    },
]


# Slug is generated from the title, so these keys match what Post.save() builds.
# Each tuple is (username, body, days_ago) — the username must exist in PEOPLE.
COMMENTS = {
    'the-n1-query-is-the-most-expensive-bug-you-will-never-see': [
        ('rohan_dev', 'Found three of these in our admin views ten minutes after reading this. One list page went from 240 queries to 4.', 3),
        ('meghana', 'The assertNumQueries tip is the part people skip. Debug Toolbar catches it once, the test catches it forever.', 2),
        ('sanjay.k', 'Counterpoint on prefetch_related: it is easy to over-prefetch and pull half the database into memory. Measure both sides.', 1),
    ],
    'your-next-migration-is-a-production-outage': [
        ('half_awake_ops', 'The lock queue explanation is the clearest I have read. We lost 20 minutes to exactly this and blamed the ALTER instead of the report query in front of it.', 12),
        ('priya', 'Adding lock_timeout to our migration runner this week. No reason not to.', 9),
    ],
    'most-sites-do-not-need-a-frontend-framework': [
        ('t.builds', 'Agree on the marketing site. Disagree that islands scale, the moment two islands need shared state you have rebuilt the framework badly.', 20),
        ('nikhil', 'Shipped a Django plus htmx rewrite of a React admin last quarter. Same features, a tenth of the code, nobody has complained once.', 18),
        ('ana_m', 'The 2019 bundler line hurt. My old project cannot even be installed anymore.', 14),
    ],
    'nobody-reads-your-logs-including-you': [
        ('devika', 'Request ids in the response header is such a small thing and it makes support tickets ten times faster to answer.', 40),
        ('marcus', 'Our ERROR channel fires about 300 times a day. Reading this was uncomfortable.', 35),
    ],
    'a-pull-request-is-not-a-code-review': [
        ('sam.qa', 'The nit / question / blocking prefixes changed our review culture more than any process doc did.', 55),
        ('irfan', 'Small PRs are a skill, not a policy. Took me a year to learn how to split work so the pieces actually ship on their own.', 51),
    ],
    'your-dev-environment-is-a-science-experiment': [
        ('lena', 'The onboarding stopwatch is brutal and correct. We found six broken steps the first time we tried it.', 70),
        ('bhaskar', 'Services in Docker, app on the host, is exactly where we landed after two years of arguing about it.', 66),
    ],
    'the-database-is-not-a-queue': [
        ('half_awake_ops', 'We ran the naive version for eight months before anyone noticed the duplicate charges. SKIP LOCKED the same week we found it.', 84),
        ('priya', 'The point about it breaking statistically rather than loudly is the part I will be quoting in design reviews.', 80),
        ('sam.qa', 'Counterpoint: the lease timestamp is doing a lot of work in that recommendation and it is the bit everyone forgets.', 74),
    ],
    'half-your-tests-are-testing-django': [
        ('irfan', 'Deleted forty tests after reading this. Suite went from 90 seconds to 31 and I do not miss any of them.', 96),
        ('devika', 'setUpTestData versus setUp is genuinely the cheapest speedup in a Django suite and almost nobody knows it exists.', 92),
        ('t.builds', 'Disagree slightly on coverage. It is a bad goal but a good tripwire on files that should never be untested.', 88),
    ],
    'caching-is-a-bet-about-the-future': [
        ('marcus', 'Caching an N+1 does not fix the N+1. Putting that on a poster above the desk.', 112),
        ('ana_m', 'The stampede section deserves its own article. We took an outage from exactly this after a routine deploy.', 106),
    ],
}
