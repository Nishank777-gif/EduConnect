-- =============================================================================
-- EduConnect Seed Data
-- Verified educational organisations, categories, and real free courses
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Insert Categories (8 Core Academic & Tech Topics)
-- -----------------------------------------------------------------------------
INSERT INTO categories (name, icon, description) VALUES
('Programming', '💻', 'Software development, Python, JavaScript, and coding languages'),
('Computer Science', '🧠', 'Algorithms, data structures, operating systems, and computing theory'),
('Mathematics', '📐', 'Algebra, calculus, statistics, linear algebra, and discrete math'),
('Science', '🔬', 'Physics, chemistry, biology, and scientific fundamentals'),
('Business Studies', '📊', 'Economics, entrepreneurship, management, and finance'),
('English', '📚', 'Language proficiency, grammar, professional communication, and writing'),
('Technology', '⚙️', 'Artificial intelligence, cloud computing, cybersecurity, and data analytics'),
('Competitive Examinations', '🎯', 'Aptitude, reasoning, general knowledge, and exam preparation')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- -----------------------------------------------------------------------------
-- 2. Insert Top 10 Educational Organisations
-- -----------------------------------------------------------------------------
INSERT INTO organizations (name, description, website_url, subjects, pricing_type, rating, total_votes) VALUES
('Khan Academy', 'A nonprofit providing free, world-class education for anyone, anywhere through interactive exercises, videos, and a personalized learning dashboard.', 'https://www.khanacademy.org', 'Math, Science, Computing, Economics', 'Free', 4.90, 1420),
('freeCodeCamp', 'A donor-supported nonprofit that helps millions learn to code for free with hands-on interactive projects and verified developer certifications.', 'https://www.freecodecamp.org', 'Programming, Web Dev, Python, Data Science', 'Free', 4.90, 1650),
('MIT OpenCourseWare', 'A web-based publication of virtually all MIT course content, open and freely accessible to everyone around the globe.', 'https://ocw.mit.edu', 'Computer Science, Mathematics, Physics, Engineering', 'Free', 4.80, 980),
('Coursera', 'A global online learning platform partnering with 275+ leading universities to offer free-to-audit university courses.', 'https://www.coursera.org', 'Computer Science, Business, Data Science, AI', 'Freemium', 4.70, 1120),
('edX', 'An online learning destination founded by Harvard and MIT offering free-to-audit courses from top worldwide institutions.', 'https://www.edx.org', 'Computer Science, Engineering, Business, Humanities', 'Freemium', 4.70, 890),
('Stanford Online', 'Stanford University portal offering free access to select lectures, engineering courses, and public educational material.', 'https://online.stanford.edu', 'Artificial Intelligence, Algorithms, Health, Engineering', 'Free', 4.80, 750),
('Harvard Online', 'Harvard University digital learning initiative offering world-renowned open courses including CS50 and humanities lectures.', 'https://online-learning.harvard.edu', 'Computer Science, Data Analysis, Humanities, Law', 'Free', 4.80, 940),
('Kaggle Learn', 'Hands-on practical micro-courses in machine learning, Python, Pandas, and deep learning with immediate browser-based coding environments.', 'https://www.kaggle.com/learn', 'Data Science, Machine Learning, Python, SQL', 'Free', 4.80, 810),
('OpenStax', 'Rice University educational nonprofit publishing openly licensed, peer-reviewed educational learning materials for college students.', 'https://openstax.org', 'Mathematics, Physics, Biology, Economics', 'Free', 4.60, 530),
('W3Schools', 'The world-famous web developer site featuring simple, beginner-friendly tutorials, code references, and interactive "Try-It" sandboxes.', 'https://www.w3schools.com', 'HTML, CSS, JavaScript, SQL, Python', 'Free', 4.50, 920)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- -----------------------------------------------------------------------------
-- 3. Insert Verified Free Courses
-- -----------------------------------------------------------------------------
INSERT INTO courses (organization_id, category_id, title, description, duration, certificate_available, course_url) VALUES
-- Course 1: CS50x (Harvard / CS category)
(7, 2, 'CS50: Introduction to Computer Science', 'An entry-level course teaching how to think algorithmically and solve problems efficiently using C, Python, SQL, and web technologies.', '12 Weeks (Self-paced)', TRUE, 'https://cs50.harvard.edu/x/'),

-- Course 2: Scientific Computing with Python (freeCodeCamp / Programming category)
(2, 1, 'Scientific Computing with Python', 'Master Python fundamentals, loops, data structures, algorithms, and build 5 required portfolio projects for a free certificate.', '300 Hours (Self-paced)', TRUE, 'https://www.freecodecamp.org/learn/scientific-computing-with-python/'),

-- Course 3: Calculus 1A: Differentiation (MIT OCW / Mathematics category)
(3, 3, 'Calculus 1A: Differentiation', 'Fundamental calculus course covering limits, derivatives, chain rule, implicit differentiation, and optimization problems.', '10 Weeks', FALSE, 'https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/'),

-- Course 4: Introduction to Relational Databases and SQL (Khan Academy / Programming category)
(1, 1, 'Intro to SQL: Querying and Managing Data', 'Learn how to use SQL to store, query, and manipulate data with interactive live challenges in a relational database browser.', '6 Hours (Self-paced)', FALSE, 'https://www.khanacademy.org/computing/computer-programming/sql'),

-- Course 5: Machine Learning Explainability (Kaggle Learn / Technology category)
(8, 7, 'Machine Learning Explainability', 'Extract real-world insights from machine learning models using permutation importance, SHAP values, and partial dependence plots.', '4 Hours (Self-paced)', TRUE, 'https://www.kaggle.com/learn/machine-learning-explainability'),

-- Course 6: English for Career Development (Coursera / edX / English category)
(4, 6, 'English for Career Development', 'Designed for non-native English speakers to navigate job search processes, craft effective resumes, and excel in professional interviews.', '5 Weeks (Free Audit)', FALSE, 'https://www.coursera.org/learn/careerdevelopment'),

-- Course 7: Introduction to Business (OpenStax / Coursera / Business Studies category)
(9, 5, 'Principles of Management and Business', 'Explores foundational business management principles, ethical practices, organizational behavior, and global market dynamics.', '8 Weeks', FALSE, 'https://openstax.org/details/books/principles-management'),

-- Course 8: Responsive Web Design (freeCodeCamp / Programming category)
(2, 1, 'Responsive Web Design Certification', 'Learn modern HTML5, CSS3, Flexbox, CSS Grid, and responsive layout techniques by building 5 accessible web applications.', '300 Hours (Self-paced)', TRUE, 'https://www.freecodecamp.org/learn/2022/responsive-web-design/'),

-- Course 9: General Physics I: Classical Mechanics (MIT OCW / Science category)
(3, 4, 'Classical Mechanics (8.01SC)', 'Comprehensive university physics course covering Newton laws of motion, gravitation, rotational dynamics, and energy conservation.', '12 Weeks', FALSE, 'https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/'),

-- Course 10: Quantitative Aptitude & Exam Prep (Khan Academy / Competitive Exams)
(1, 8, 'Quantitative Aptitude and Problem Solving', 'Master numerical reasoning, percentages, ratios, probability, and analytical problem-solving required for competitive tests.', 'Self-paced', FALSE, 'https://www.khanacademy.org/math/algebra')
ON DUPLICATE KEY UPDATE title=VALUES(title);
