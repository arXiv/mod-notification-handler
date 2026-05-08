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

-- archive exclusion test: 77777 mods astro-ph archive but opts out of astro-ph.HE specifically
INSERT INTO `tapir_users` VALUES (77777,'Archive','OptOut','',1,1,'archive-optout@example.com',8,0,2,1384185389,'dedicated','',0,0,0,1,1,0,0,0,0,'',0,0);
INSERT INTO `arXiv_moderators` VALUES (77777, 'astro-ph', '', 0, 0, 0, 0, 0);
INSERT INTO `arXiv_moderators` VALUES (77777, 'astro-ph', 'HE', 0, 1, 0, 0, 0);
