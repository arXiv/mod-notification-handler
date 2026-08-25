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
