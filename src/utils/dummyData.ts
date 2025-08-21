// Types for our data models
export interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone: string;
  location: string;
  school: string;
  grade: string;
  bio: string;
  interests: string[];
  availability: {
    weekdays: string;
    weekends: string;
    summer: string;
  };
  profileImage: string;
  userType: 'student' | 'organization';
  password: string; // In a real app, we would never store plaintext passwords
}
export interface Organization {
  id: number;
  name: string;
  email: string;
  phone: string;
  location: string;
  description: string;
  website: string;
  logo: string;
  userType: 'organization';
  password: string; // In a real app, we would never store plaintext passwords
}
export interface Opportunity {
  id: number;
  title: string;
  organization: string;
  organizationId: number;
  location: string;
  type: string;
  category: string;
  date: string;
  hours: string;
  deadline: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  benefits: string[];
  image: string;
  orgLogo: string;
  createdAt: string;
}
// Dummy users data
export const users: UserProfile[] = [{
  id: 1,
  name: 'Alex Johnson',
  email: 'alex@example.com',
  phone: '(555) 123-4567',
  location: 'San Francisco, CA',
  school: 'Lincoln High School',
  grade: '11th Grade',
  bio: "I'm a high school student interested in technology and environmental conservation. Looking for opportunities to gain experience and make a difference in my community.",
  interests: ['Web Development', 'Environmental Science', 'Graphic Design', 'Community Service'],
  availability: {
    weekdays: 'After 3:30 PM',
    weekends: 'Flexible',
    summer: 'Full-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1568602471122-7832951cc4c5?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80',
  userType: 'student',
  password: 'password123' // In a real app, this would be hashed
}, {
  id: 2,
  name: 'Taylor Smith',
  email: 'taylor@example.com',
  phone: '(555) 987-6543',
  location: 'Chicago, IL',
  school: 'Westside High School',
  grade: '10th Grade',
  bio: "I'm passionate about helping others and interested in pursuing a career in healthcare. I enjoy volunteering and learning new skills.",
  interests: ['Healthcare', 'Biology', 'Volunteering', 'Photography'],
  availability: {
    weekdays: 'After 4:00 PM',
    weekends: 'Saturday mornings',
    summer: 'Part-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=774&q=80',
  userType: 'student',
  password: 'password123'
}, {
  id: 3,
  name: 'Jordan Lee',
  email: 'jordan@example.com',
  phone: '(555) 456-7890',
  location: 'Seattle, WA',
  school: 'Roosevelt High School',
  grade: '12th Grade',
  bio: "Aspiring software engineer with a passion for AI and robotics. I've participated in several hackathons and enjoy building projects that solve real-world problems.",
  interests: ['Programming', 'Artificial Intelligence', 'Robotics', 'Mathematics'],
  availability: {
    weekdays: 'After 2:30 PM',
    weekends: 'Anytime',
    summer: 'Full-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=774&q=80',
  userType: 'student',
  password: 'password123'
}, {
  id: 4,
  name: 'Morgan Chen',
  email: 'morgan@example.com',
  phone: '(555) 234-5678',
  location: 'Boston, MA',
  school: 'Boston Latin School',
  grade: '11th Grade',
  bio: "I'm interested in journalism and digital media. I serve as the editor for my school newspaper and am looking to gain more experience in content creation and marketing.",
  interests: ['Journalism', 'Digital Media', 'Writing', 'Social Media'],
  availability: {
    weekdays: 'After 3:00 PM',
    weekends: 'Sunday afternoons',
    summer: 'Part-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80',
  userType: 'student',
  password: 'password123'
}, {
  id: 5,
  name: 'Riley Washington',
  email: 'riley@example.com',
  phone: '(555) 345-6789',
  location: 'Austin, TX',
  school: 'Austin High School',
  grade: '10th Grade',
  bio: 'Passionate about music and the arts. I play guitar in a band and am interested in audio production and sound engineering. Looking to connect with others who share similar interests.',
  interests: ['Music Production', 'Audio Engineering', 'Guitar', 'Digital Arts'],
  availability: {
    weekdays: 'After 4:30 PM',
    weekends: 'Flexible',
    summer: 'Full-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=774&q=80',
  userType: 'student',
  password: 'password123'
}, {
  id: 6,
  name: 'Quinn Rodriguez',
  email: 'quinn@example.com',
  phone: '(555) 567-8901',
  location: 'Miami, FL',
  school: 'Miami Senior High School',
  grade: '9th Grade',
  bio: "Interested in business and entrepreneurship. I've started a small online business selling handmade crafts and am eager to learn more about marketing and finance.",
  interests: ['Entrepreneurship', 'Business', 'Marketing', 'Design'],
  availability: {
    weekdays: 'After 3:00 PM',
    weekends: 'Saturday afternoons',
    summer: 'Part-time'
  },
  profileImage: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1064&q=80',
  userType: 'student',
  password: 'password123'
}];
// Dummy organizations data
export const organizations: Organization[] = [{
  id: 101,
  name: 'TechStart Solutions',
  email: 'contact@techstart.org',
  phone: '(555) 234-5678',
  location: 'San Francisco, CA',
  description: 'TechStart Solutions is a nonprofit organization dedicated to helping young people develop technology skills through internships and mentoring programs.',
  website: 'www.techstart.org',
  logo: 'https://images.unsplash.com/photo-1549921296-bc643ead1e65?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1150&q=80',
  userType: 'organization',
  password: 'orgpassword123'
}, {
  id: 102,
  name: 'Green Earth Initiative',
  email: 'info@greenearthinitiative.org',
  phone: '(555) 876-5432',
  location: 'Portland, OR',
  description: 'Green Earth Initiative works to protect and restore natural environments through community action, education, and sustainable practices.',
  website: 'www.greenearthinitiative.org',
  logo: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1171&q=80',
  userType: 'organization',
  password: 'orgpassword123'
}];
// Dummy opportunities data
export const opportunities: Opportunity[] = [{
  id: 1,
  title: 'Web Development Intern',
  organization: 'TechStart Solutions',
  organizationId: 101,
  location: 'San Francisco, CA',
  type: 'Internship',
  category: 'Technology',
  date: 'Summer 2023 (June 15 - August 15)',
  hours: '15-20 hrs/week',
  deadline: '2023-05-15',
  description: "TechStart Solutions is looking for motivated high school students interested in learning web development. As an intern, you'll work alongside our development team to build and maintain websites for our clients. This is a great opportunity to gain hands-on experience in a professional environment while developing valuable skills in HTML, CSS, JavaScript, and more.",
  responsibilities: ['Assist in coding and testing new website features', 'Help maintain and update existing client websites', 'Participate in team meetings and brainstorming sessions', 'Learn modern web development frameworks and techniques', 'Document your work and contribute to project documentation'],
  requirements: ['Interest in computer science and web development', 'Basic understanding of HTML and CSS (JavaScript a plus)', 'Strong problem-solving skills and attention to detail', 'Ability to commit to 15-20 hours per week during the summer', 'Reliable transportation to our office in San Francisco'],
  benefits: ['Hands-on experience with real-world projects', 'Mentorship from experienced developers', 'Exposure to professional work environment', 'Certificate of completion', 'Potential for school credit (check with your school counselor)'],
  image: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2072&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1549921296-bc643ead1e65?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1150&q=80',
  createdAt: '2023-04-01'
}, {
  id: 2,
  title: 'Environmental Conservation Volunteer',
  organization: 'Green Earth Initiative',
  organizationId: 102,
  location: 'Portland, OR',
  type: 'Volunteer',
  category: 'Environment',
  date: 'Ongoing',
  hours: '5-10 hrs/week',
  deadline: '2023-12-31',
  description: "Join Green Earth Initiative's team of volunteers dedicated to protecting and restoring natural environments in the Portland area. Volunteers will participate in various conservation activities including trail maintenance, invasive species removal, native planting, and community education events. This is a perfect opportunity for students interested in environmental science, conservation, or those who simply want to make a difference in their community.",
  responsibilities: ['Participate in conservation projects at local parks and natural areas', 'Help with invasive species removal and native plant restoration', 'Assist with community education events and workshops', 'Collect data for environmental monitoring projects', 'Contribute to our social media and outreach efforts'],
  requirements: ['Passion for environmental conservation', 'Willingness to work outdoors in various weather conditions', 'Ability to perform physical tasks such as digging, planting, and lifting', 'Commitment to at least 5 hours per week', 'Reliable transportation to project sites in Portland area'],
  benefits: ['Make a tangible difference in local ecosystems', 'Learn about environmental science and conservation techniques', 'Develop leadership and teamwork skills', 'Community service hours for school requirements', 'Networking opportunities with environmental professionals'],
  image: 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2013&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1171&q=80',
  createdAt: '2023-03-15'
}, {
  id: 3,
  title: 'Marketing Assistant',
  organization: 'Bright Ideas Marketing',
  organizationId: 103,
  location: 'Chicago, IL',
  type: 'Internship',
  category: 'Marketing',
  date: 'Fall 2023',
  hours: '10-15 hrs/week',
  deadline: '2023-08-15',
  description: "Bright Ideas Marketing is seeking a creative and enthusiastic high school student to join our team as a Marketing Assistant intern. In this role, you'll support our marketing team with social media management, content creation, and basic market research. This internship offers a fantastic opportunity to gain hands-on experience in digital marketing while developing valuable skills for future career opportunities.",
  responsibilities: ['Assist with creating and scheduling social media content', 'Help design basic graphics and visual content', 'Support the team with market research and competitor analysis', 'Contribute ideas for marketing campaigns and content', 'Track and report on social media metrics'],
  requirements: ['Interest in marketing, communications, or business', 'Creativity and strong writing skills', 'Basic familiarity with social media platforms', 'Ability to commit to 10-15 hours per week during the fall semester', 'Self-motivated with good time management skills'],
  benefits: ['Practical experience in digital marketing', 'Portfolio development opportunities', 'Mentorship from marketing professionals', 'Flexible schedule to accommodate school commitments', 'Potential for school credit and letter of recommendation'],
  image: 'https://images.unsplash.com/photo-1551434678-e076c223a692?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1171&q=80',
  createdAt: '2023-04-10'
}, {
  id: 4,
  title: 'Youth Mentor',
  organization: 'Community Youth Center',
  organizationId: 104,
  location: 'Boston, MA',
  type: 'Volunteer',
  category: 'Education',
  date: 'Fall 2023',
  hours: '5 hrs/week',
  deadline: '2023-09-01',
  description: 'The Community Youth Center is looking for responsible and compassionate high school students to serve as mentors for elementary and middle school students. Mentors will provide academic support, engage in recreational activities, and serve as positive role models. This is an excellent opportunity for students interested in education, psychology, or social work to make a meaningful impact on younger students in their community.',
  responsibilities: ['Provide one-on-one or small group homework help', 'Lead and participate in educational games and activities', 'Serve as a positive role model for younger students', 'Help create a safe and supportive environment', 'Communicate with program staff about student progress'],
  requirements: ['Patience and ability to work well with children', 'Strong communication and interpersonal skills', 'Reliability and commitment to scheduled sessions', 'Minimum GPA of 3.0', 'Successful completion of background check'],
  benefits: ['Develop leadership and mentoring skills', 'Make a positive impact on younger students', 'Gain experience for college applications and future careers', 'Community service hours for school requirements', 'Training in youth development and education techniques'],
  image: 'https://images.unsplash.com/photo-1529390079861-591de354faf5?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1536337005238-94b997371b40?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1169&q=80',
  createdAt: '2023-05-01'
}, {
  id: 5,
  title: 'Research Assistant',
  organization: 'City Science Museum',
  organizationId: 105,
  location: 'Seattle, WA',
  type: 'Internship',
  category: 'Science',
  date: 'Summer 2023',
  hours: '20 hrs/week',
  deadline: '2023-05-30',
  description: "The City Science Museum is offering a summer internship program for high school students interested in science education and research. As a Research Assistant intern, you'll help our education team develop new interactive exhibits, assist with visitor studies, and support ongoing research projects. This internship provides valuable experience in scientific research, education, and museum operations.",
  responsibilities: ['Assist with the development and testing of new museum exhibits', 'Help conduct visitor surveys and analyze feedback data', 'Support education staff with program materials and activities', 'Contribute to research projects in collaboration with museum scientists', 'Assist with special events and educational workshops'],
  requirements: ['Strong interest in science and education', 'Excellent attention to detail and research skills', 'Ability to communicate scientific concepts clearly', 'Availability for 20 hours per week during summer months', 'Comfortable interacting with museum visitors of all ages'],
  benefits: ['Hands-on experience in science education and research', 'Exposure to museum operations and exhibit development', 'Mentorship from professional scientists and educators', 'Museum membership during internship period', 'Stipend of $500 upon successful completion of the program'],
  image: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1503387837-b154d5074bd2?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1331&q=80',
  createdAt: '2023-04-15'
}, {
  id: 6,
  title: 'Healthcare Volunteer',
  organization: 'Memorial Hospital',
  organizationId: 106,
  location: 'Denver, CO',
  type: 'Volunteer',
  category: 'Healthcare',
  date: 'Year-round',
  hours: '4-8 hrs/week',
  deadline: '2023-12-31',
  description: "Memorial Hospital's High School Volunteer Program offers students interested in healthcare careers an opportunity to gain firsthand experience in a hospital setting. Volunteers support hospital staff and patients in various departments, including the information desk, gift shop, and patient floors. This program provides valuable exposure to healthcare professions while making a positive impact on patient experience.",
  responsibilities: ['Assist visitors with information and directions', 'Deliver flowers, mail, and other items to patient rooms', 'Support staff with administrative tasks', 'Transport patients in wheelchairs when needed', 'Help with special events and hospital initiatives'],
  requirements: ['Minimum age of 16', 'Interest in healthcare or medical field', 'Commitment to at least 4 hours per week for 3 months', 'Completion of hospital volunteer orientation', 'Up-to-date immunizations including flu and COVID-19 vaccines'],
  benefits: ['Exposure to various healthcare careers', 'Experience in a professional healthcare environment', 'Development of patient interaction skills', 'Community service hours for school requirements', 'Letter of recommendation upon completion of 50+ hours'],
  image: 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1153&q=80',
  orgLogo: 'https://images.unsplash.com/photo-1519494080410-f9aa76cb4283?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1153&q=80',
  createdAt: '2023-03-01'
}];
// Function to authenticate a user
export const authenticateUser = (email: string, password: string) => {
  // Check students
  const student = users.find(user => user.email === email && user.password === password);
  if (student) {
    return {
      user: student,
      userType: 'student'
    };
  }
  // Check organizations
  const organization = organizations.find(org => org.email === email && org.password === password);
  if (organization) {
    return {
      user: organization,
      userType: 'organization'
    };
  }
  return null;
};