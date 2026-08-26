-- Tapir Users

-- admin users
INSERT INTO `tapir_users` VALUES (246231,'Brandon','Barker','',1,1,'no-mail@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'cpe-24-59.res.rr.com.1372902602452690',0,0);
INSERT INTO `arXiv_moderators` VALUES (246231,'q-bio','CB','0','0','0','0','0');
INSERT INTO `arXiv_moderators` VALUES (246231,'q-bio','NC','0','0','0','0','0');
INSERT INTO `arXiv_moderators` VALUES (246231,'q-bio', '','0','0','0','0','0');

--developer moderator(shamsi) with special access to queues
INSERT INTO `tapir_users` VALUES (681201,'Shams','Brinn','',1,1,'also-dont-mail@example.com',8,0,2,1384185389,'net','',0,0,0,1,1,0,0,0,0,'cpe-24-59.com.1372902602452690',0,0);
INSERT INTO `arXiv_moderators` VALUES (681201,'q-bio','NC','0','0','0','0','0'); 

INSERT INTO `tapir_users` VALUES (1234544,'Mod','Devs','',1,1,'dont-mail@example.com',8,0,2,1384185389,'net','',0,0,0,1,1,0,0,0,0,'cpe-24-59.com.1372902602452690',0,0);
INSERT INTO `arXiv_moderators` VALUES (1234544,'q-bio','NC','0','0','0','0','0'); 

INSERT INTO `tapir_users` VALUES (246232,'Lo','Jack','',1,1,'other-no-mail@example.com',8,0,2,1384185389,'net','',0,0,0,1,1,0,0,0,0,'cpe-24-59.com.1372902602452690',0,0);
INSERT INTO `arXiv_moderators` VALUES (246232,'q-bio','NC','0','0','0','0','0');
INSERT INTO `arXiv_moderators` VALUES (246232,'q-fin','','0','0','0','0','0');

INSERT INTO `tapir_users` VALUES (246233,'Frank','Franky','',1,1,'no-mailx234@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'cpe-24-59.res.rr.com.1372902602452690',0,0);
INSERT INTO `arXiv_moderators` VALUES (246233,'hep-ph', '','0','0','0','0','0');
INSERT INTO `tapir_nicknames` VALUES (246210,'ffrky',246233,1,1,0,0,1);

INSERT INTO `tapir_users` VALUES (9999,'Ralf','W','',1,1,'no-mail-rw@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);

INSERT INTO `arXiv_moderators` VALUES (9999, 'astro-ph', '', '0' , '0' , '0' , '0' , '0' );
INSERT INTO `arXiv_moderators` VALUES (9999, 'astro-ph', 'HE', 1 , '0' , '0' , '0' , '0' );
INSERT INTO `arXiv_moderators` VALUES (9999, 'cond-mat', '', '0' , '0' , '0' , '0' , '0' );
INSERT INTO `arXiv_moderators` VALUES (9999, 'physics', '', '0' , '0' , '0' , '0' , '0' );

-- email/reply-to flag test users 
INSERT INTO `tapir_users` VALUES (50001,'No','Email','',1,1,'noemail@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `tapir_users` VALUES (50002,'No','WebEmail','',1,1,'nowebemail@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `tapir_users` VALUES (50003,'No','ReplyTo','',1,1,'noreplyto@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `tapir_users` VALUES (50004,'Normal','Mod','',1,1,'normal@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (50001, 'cs', 'AI', 0, 1, 0, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (50002, 'cs', 'AI', 0, 0, 1, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (50003, 'cs', 'AI', 0, 0, 0, 1, 0);
INSERT INTO `arXiv_moderators` VALUES (50004, 'cs', 'AI', 0, 0, 0, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (50004, 'cs', '',  0, 0, 0, 0, 0);

-- archive exclusion test: 77777 mods astro-ph archive but fully opts out of astro-ph.HE (no email, no reply-to)
INSERT INTO `tapir_users` VALUES (77777,'Archive','OptOut','',1,1,'archive-optout@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (77777, 'astro-ph', '', 0, 0, 0, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (77777, 'astro-ph', 'HE', 0, 1, 0, 1, 0);

-- category alias tests: q-fin.EC is the alias of canonical category econ.GN
INSERT INTO `tapir_users` VALUES (60001,'Alias','CatMod','',1,1,'aliascat@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (60001, 'q-fin', 'EC', 0, 0, 0, 0, 0);

-- 60002 opts out of named category econ.GN and would otherwise qualify via the alias archive (q-fin)
INSERT INTO `tapir_users` VALUES (60002,'Cascade','OptOut','',1,1,'cascadeoptout@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (60002, 'econ', 'GN', 0, 1, 0, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (60002, 'q-fin', '', 0, 0, 0, 0, 0);

-- actor users referenced in test messages (user_id=1 and user_id=2)
INSERT INTO `tapir_users` VALUES (1,'Test','Editor','',1,1,'editor-one@example.com',8,0,2,1384185389,'','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `tapir_users` VALUES (2,'Jane','Smith','',1,1,'editor-two@example.com',8,0,2,1384185389,'','',0,0,0,1,1,0,0,0,0,'',0,0);

-- nicknames for key test users (nick_id, nickname, user_id, user_seq, flag_valid, role, policy, flag_primary)
INSERT INTO `tapir_nicknames` VALUES (10001,'bbarker',246231,1,1,0,0,1);
INSERT INTO `tapir_nicknames` VALUES (10002,'shamsi',681201,1,1,0,0,1);
INSERT INTO `tapir_nicknames` VALUES (10003,'moddevs',1234544,1,1,0,0,1);
INSERT INTO `tapir_nicknames` VALUES (10004,'testeditor',1,1,1,0,0,1);
INSERT INTO `tapir_nicknames` VALUES (10005,'jsmith',2,1,1,0,0,1);

-- test submissions used in integration tests
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, remote_addr, remote_host, package) VALUES (123, 'A Test Paper on Machine Learning', 'Author One, Author Two', 1, '127.0.0.1', 'localhost', '');
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, remote_addr, remote_host, package) VALUES (124, 'Another Test Paper on Category Promotion', 'Author Three', 1, '127.0.0.1', 'localhost', '');
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, remote_addr, remote_host, package) VALUES (125, 'Paper With No Categories', 'Some Author', 1, '127.0.0.1', 'localhost', '');
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, remote_addr, remote_host, package) VALUES (126, 'A Math-Physics Paper', 'Author Math', 1, '127.0.0.1', 'localhost', '');

-- submission categories for get_submission_info tests
-- 123: cs.LG primary + cs.AI cross-list
INSERT INTO `arXiv_submission_category` VALUES (123, 'cs.LG', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (123, 'cs.AI', 0, NULL);
-- 124: no primary, two cross-list
INSERT INTO `arXiv_submission_category` VALUES (124, 'cs.AI', 0, NULL);
INSERT INTO `arXiv_submission_category` VALUES (124, 'cs.LG', 0, NULL);
-- 125: no categories
-- 126: math-ph primary (math.MP alias should also appear)
INSERT INTO `arXiv_submission_category` VALUES (126, 'math-ph', 1, NULL);

-- ══ daily_update digest ══════════════════════════════════════════════════════
-- moderators: last column is daily_update
-- (user_id, archive, subject_class, is_public, no_email, no_web_email, no_reply_to, daily_update)

-- two moderators of the same category
INSERT INTO `tapir_users` VALUES (55001,'Digest','CatMod','',1,1,'digest-cat@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55001, 'cs', 'AI', 0, 0, 0, 0, 1);
INSERT INTO `tapir_users` VALUES (55006,'Digest','CatModTwo','',1,1,'digest-cat2@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55006, 'cs', 'AI', 0, 0, 0, 0, 1);

-- whole-archive moderator
INSERT INTO `tapir_users` VALUES (55002,'Digest','ArchiveMod','',1,1,'digest-archive@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55002, 'astro-ph', '', 0, 0, 0, 0, 1);

-- mods the canonical category econ.GN, so should also cover its q-fin.EC alias
INSERT INTO `tapir_users` VALUES (55003,'Digest','AliasMod','',1,1,'digest-alias@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55003, 'econ', 'GN', 0, 0, 0, 0, 1);

-- no_email is set AND daily_update is set: the digest still goes out
INSERT INTO `tapir_users` VALUES (55004,'Digest','NoEmailMod','',1,1,'digest-noemail@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55004, 'nlin', 'AO', 0, 1, 0, 0, 1);

-- mods an archive with no seeded submissions, for the empty-digest case
INSERT INTO `tapir_users` VALUES (55005,'Digest','EmptyMod','',1,1,'digest-empty@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (55005, 'gr-qc', '', 0, 0, 0, 0, 1);

-- ── submissions (200s). one per rule the digest applies ─────────────────────
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (201, 'A New Submission', 'New Author', 1, 'new', '2026-07-27 10:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 203: cs.LG already announced, cs.AI is the cross being requested
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (203, 'A Cross Into cs.AI', 'Cross Author', 1, 'cross', '2026-07-27 12:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 204: withdrawal, excluded by type even though it is on a mod hold
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (204, 'A Withdrawal On Hold', 'Wdr Author', 2, 'wdr', '2026-07-27 13:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 206: no type at all. unverified that a submitted row can look like this — item K
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (206, 'A Legacy Submission', 'Odd Author', 1, NULL, '2026-07-27 15:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 207: already announced, excluded by the open-status query
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (207, 'An Already Announced Paper', 'Done Author', 7, 'new', '2026-07-27 16:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 209: on an ADMIN hold, excluded
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (209, 'On Admin Hold', 'Admin Hold Author', 2, 'new', '2026-07-27 18:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 210: on a MOD hold, included and belongs in the HOLD section
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (210, 'On Mod Hold', 'Mod Hold Author', 2, 'rep', '2026-07-27 19:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 211: test primary with a real secondary, excluded on the primary
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (211, 'A Test Category Paper', 'Test Author', 1, 'new', '2026-07-27 20:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 212: journal reference, excluded by type
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (212, 'A Journal Reference', 'Jref Author', 1, 'jref', '2026-07-27 21:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 213: has comments and unresolved proposals, for the entry line
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (213, 'A Discussed Paper', 'Talky Author', 1, 'new', '2026-07-27 22:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
-- 214: cross where cs.AI is ALREADY announced and cs.LG is the new one. a cs.AI mod must NOT see it
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (214, 'A Cross Out Of cs.AI', 'Other Cross Author', 1, 'cross', '2026-07-27 23:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');

-- categories: (submission_id, category, is_primary, is_published)
INSERT INTO `arXiv_submission_category` VALUES (201, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (203, 'cs.LG', 1, 1);
INSERT INTO `arXiv_submission_category` VALUES (203, 'cs.AI', 0, 0);
INSERT INTO `arXiv_submission_category` VALUES (204, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (206, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (207, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (209, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (210, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (211, 'test.dis-nn', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (211, 'cs.AI', 0, NULL);
INSERT INTO `arXiv_submission_category` VALUES (212, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (213, 'cs.AI', 1, NULL);
INSERT INTO `arXiv_submission_category` VALUES (214, 'cs.AI', 1, 1);
INSERT INTO `arXiv_submission_category` VALUES (214, 'cs.LG', 0, 0);

-- holds: (reason_id, submission_id, user_id, reason, type, comment_id)
INSERT INTO `arXiv_submission_hold_reason` VALUES (1, 209, 246231, 'scope', 'admin', NULL);
INSERT INTO `arXiv_submission_hold_reason` VALUES (2, 210, 246231, 'discussion', 'mod', NULL);
-- 204 is a wdr on a mod hold: excluded by type, not by hold
INSERT INTO `arXiv_submission_hold_reason` VALUES (3, 204, 246231, 'discussion', 'mod', NULL);


-- proposals: (proposal_id, submission_id, category, is_primary, proposal_status, user_id, ...)
-- 0 = unresolved, 3 = rejected
INSERT INTO `arXiv_submission_category_proposal` (proposal_id, submission_id, category, is_primary, proposal_status, user_id) VALUES (1, 213, 'cs.CV', 1, 0, 246231);
INSERT INTO `arXiv_submission_category_proposal` (proposal_id, submission_id, category, is_primary, proposal_status, user_id) VALUES (2, 213, 'stat.ML', 0, 0, 246231);
INSERT INTO `arXiv_submission_category_proposal` (proposal_id, submission_id, category, is_primary, proposal_status, user_id) VALUES (3, 213, 'math.NA', 0, 3, 246231);

-- 218: still WORKING, the submitter hasn't submitted it. never in the open queue
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (218, 'Still Being Written', 'Busy Author', 0, 'new', '2026-07-28 02:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
INSERT INTO `arXiv_submission_category` VALUES (218, 'cs.AI', 1, NULL);

-- 217: legacy hold — on hold with no reason row. excluded, only mod holds are reported
INSERT INTO `arXiv_submissions` (submission_id, title, authors, status, type, submit_time, submitter_id, submitter_name, remote_addr, remote_host, package) VALUES (217, 'On A Legacy Hold', 'Nobody Author', 2, 'new', '2026-07-28 01:00:00', 246233, 'Frank Franky', '127.0.0.1', 'localhost', '');
INSERT INTO `arXiv_submission_category` VALUES (217, 'cs.AI', 1, NULL);

