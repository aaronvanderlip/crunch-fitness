Welcome to the Crunch.io api fitness test.

Here you will find a python package to help us evaluate your skills with:

1. Problem Solving
2. Web Server API Design
3. Request-time data manipulation
4. Testing strategies

Instructions

1. Fork the repo into a private repo.
2. Create a virtualenv for this project and install the cr-api and cr-db packages into your environment.
3. Modify the cr-api package to complete the task, the code is commented with task items.
4. Let us know when you have finished.

Deliverable

Publish your work in a GitHub repository.

* CherryPy, MongoDB, PyMongo, and WebTest were all technologies that I have not used before.
* I could not find a good example of a CherryPy testing setup that worked so I created my own.
* The test suite I created is not complete.
* There is one failing assertion for test_validate_email. See https://github.com/aaronvanderlip/crunch-fitness/blob/master/cr-api/cr/api/tests.py#L90 Either the REGEX needs to be fixed or a different approach taken.
* This pattern for delivering updates to the UI https://github.com/aaronvanderlip/crunch-fitness/blob/master/cr-api/cr/api/tests.py#L90 is a shortcut so as to not implement a template solution. I understand that it's a XSS vector. 
* I had to work around the data that was loaded by the fixture and the default insertion method for MongoDB. See https://github.com/aaronvanderlip/crunch-fitness/blob/master/cr-api/cr/api/server.py#L208-L217. I am unsure if this is part of the test or something that should be fixed. 
* I was unable to complete the distance task in a reasonable amount of time. I could not see a way of accomplishing is using only numpy. I could create a solution that calculates the distances using itertools.combination plus a haversine function cribbed from somewhere. Once I had the calculated distances I could use the numpy statistical functions to return the results.
* For purposes of evaluating prospective developers, publishing to GitHub will leak solutions over time.

    
