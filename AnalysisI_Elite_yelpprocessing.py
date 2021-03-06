# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 19:17:35 2015

@author: jeppley
"""

import json
import pandas as pd
import numpy as np
import sqlite3
from glob import glob
import re
import os
import pylab as pl
import statsmodels.api as sm
import matplotlib.pyplot as plt
from patsy import dmatrices
from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.cross_validation import cross_val_score

###############################
#####CONVERTING JSON FILES#####
###############################
def convert(x):
    ''' Convert a json string to a flat python dictionary
    which can be passed into Pandas. '''
    
    ob = json.loads(x)
    for k, v in ob.items():
        if isinstance(v, list):
            ob[k] = ','.join(str(v))
        elif isinstance(v, dict):
            for kk, vv in v.items():
                ob['%s_%s' % (k, kk)] = vv
            del ob[k]
    return ob
    
x = r"S:\m&a\SQL_STORAGE\GM GAME\Projects\GA\Project\yelp_academic_dataset_user.json"

#convert(x)
directory = r'S:\m&a\SQL_STORAGE\GM GAME\Projects\GA\Project\yelp_dataset_challenge_academic_dataset'
os.chdir(directory)
for json_filename in glob('*.json'):
    csv_filename = '%s.csv' % json_filename[:-5]
    print 'Converting %s to %s' % (json_filename, csv_filename)
    df = pd.DataFrame([convert(line) for line in file(json_filename)])
    df.to_csv(csv_filename, encoding='utf-8', index=False)

####################################################
#####PreProcessing Business and Review Data Set#####
####################################################
##reading in business data set
#looking at descriptives
csv ='Desktop\yelp_academic_dataset_business.csv'
business=pd.read_csv(csv)
business.head()
business.describe()
business.columns

#only want certain variables within data set
business2 = business[["city", "business_id", "stars", "categories"]]
business2.columns
business2.groupby(['city'])['business_id'].nunique().reset_index()
business2[['city']]
business2.head()
#subsetting to only Las Vegas
business3=business2[business2["city"] == "Las Vegas"].squeeze()
business3.head()

#Exploring variables
#Looking at stars metric to make proper success variable
business3.stars.mean()
business3.categories.describe()
business3.stars.hist(bins=20)
#decided success should be 5 stars (about 10% of sample population)

#making success variable
business3['success']=0
business3.head()
business3.success[business3.stars==5]=1
business3.success[business3.success==1]

#reading in review data set
csv2 ='Desktop\elite_tagged_reviews.csv'
review=pd.read_csv(csv2)
review.head()
review.describe()
review.columns

#merging business and review data sets
merge=pd.merge(business3, review, on='business_id', how='inner')
merge.head()
merge.to_csv(os.getcwd()+'\\Desktop\\businessreviewmerged.csv')

######################################
#####Logistic Regression Analysis#####
######################################
##ELITE REVIEWERS##
elite=merge[merge["is_elite2"] ==1].squeeze()
elite.head()
#create dataframes with an intercept column and dummy variables
y, X = dmatrices('success ~ stars_y', elite, return_type="dataframe")
print X.columns

# instantiate a logistic regression model, and fit with X and y
model = LogisticRegression()
model = model.fit(X, y)

# check the accuracy on the training set
model.score(X, y)
#0.98997785726452048
#99% accuracy seems great, but what's the null error rate?

# what percentage had successes?
y.mean()
#success    0.010022

# examine the coefficients
pd.DataFrame(zip(X.columns, np.transpose(model.coef_)))
#          0                 1
#0  Intercept  [-6.26318353752]
#1    stars_y   [1.81418418586]

# evaluate the model by splitting into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
model2 = LogisticRegression()
model2.fit(X_train, y_train)
#LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
#         intercept_scaling=1, penalty='l2', random_state=None, tol=0.0001)

# predict class labels for the test set
predicted = model2.predict(X_test)
print predicted
#[ 0.  0.  0. ...,  0.  0.  0.]

# generate class probabilities
probs = model2.predict_proba(X_test)
print probs
#[[  9.69583924e-01   3.04160759e-02]
# [  9.69583924e-01   3.04160759e-02]
# [  9.99966307e-01   3.36927831e-05]
# ..., 
# [  9.94353013e-01   5.64698724e-03]
# [  9.94353013e-01   5.64698724e-03]
# [  9.98972958e-01   1.02704242e-03]]

# generate evaluation metrics
print metrics.accuracy_score(y_test, predicted)
#0.99046169918
print metrics.roc_auc_score(y_test, probs[:, 1])
#0.82162013729
#accuracy is 99% which is the same as we experienced when training and predicting on the same data
#ROC accuracy is 82%

#We can also see the confusion matrix and a classification report with other metrics
print metrics.confusion_matrix(y_test, predicted)
print metrics.classification_report(y_test, predicted)
#[[43613     0]
# [  420     0]]
#             precision    recall  f1-score   support
#
#        0.0       0.99      1.00      1.00     43613
#        1.0       0.00      0.00      0.00       420
#
#avg / total       0.98      0.99      0.99     44033


#Now let's try 10-fold cross-validation, to see if the accuracy holds up more rigorously.
# evaluate the model using 10-fold cross-validation
from sklearn.cross_validation import KFold
cv = KFold(X.shape[0], 10, shuffle=True, random_state=33)
scores = cross_val_score(LogisticRegression(), X, y, scoring='accuracy', cv=cv)
print scores
#[ 0.98998501  0.98984875  0.9901894   0.98828178  0.98950811  0.99107447
#  0.99148327  0.99039313  0.98984806  0.98916672]

##NON-ELITE REVIEWERS##
nonelite=merge[merge["is_elite2"] ==0].squeeze()
nonelite.head()
#create dataframes with an intercept column and dummy variables
y, X = dmatrices('success ~ stars_y', nonelite, return_type="dataframe")
print X.columns

# instantiate a logistic regression model, and fit with X and y
model = LogisticRegression()
model = model.fit(X, y)

# check the accuracy on the training set
model.score(X, y)
#0.96490941004968311
#96% accuracy also seems great, but what's the null error rate?

# what percentage had successes?
y.mean()
#success    0.035091

# examine the coefficients
pd.DataFrame(zip(X.columns, np.transpose(model.coef_)))
#           0                 1
#0  Intercept  [-6.56284685163]
#1    stars_y   [2.14103519887]

# evaluate the model by splitting into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
model2 = LogisticRegression()
model2.fit(X_train, y_train)
#LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
#          intercept_scaling=1, penalty='l2', random_state=None, tol=0.0001)

# predict class labels for the test set
predicted = model2.predict(X_test)
print predicted
#[ 0.  0.  0. ...,  0.  0.  0.]

# generate class probabilities
probs = model2.predict_proba(X_test)
print probs
#[[  9.89784208e-01   1.02157918e-02]
# [  9.89784208e-01   1.02157918e-02]
# [  9.18304185e-01   8.16958153e-02]
# ..., 
# [  9.89784208e-01   1.02157918e-02]
# [  9.99983883e-01   1.61168180e-05]
# [  9.18304185e-01   8.16958153e-02]]

# generate evaluation metrics
print metrics.accuracy_score(y_test, predicted)
#0.964887550912
print metrics.roc_auc_score(y_test, probs[:, 1])
#0.789738806253
#accuracy is 96% which is the same as we experienced when training and predicting on the same data
#ROC accuracy is 79%

#We can also see the confusion matrix and a classification report with other metrics
print metrics.confusion_matrix(y_test, predicted)
print metrics.classification_report(y_test, predicted)
#[[136218      0]
# [  4957      0]]
#             precision    recall  f1-score   support
#
#        0.0       0.96      1.00      0.98    136218
#        1.0       0.00      0.00      0.00      4957
#
#avg / total       0.93      0.96      0.95    141175


#Now let's try 10-fold cross-validation, to see if the accuracy holds up more rigorously.
# evaluate the model using 10-fold cross-validation
from sklearn.cross_validation import KFold
cv = KFold(X.shape[0], 10, shuffle=True, random_state=33)
scores = cross_val_score(LogisticRegression(), X, y, scoring='accuracy', cv=cv)
print scores
#[ 0.96464013  0.96387514  0.9655744   0.96580815  0.96455438  0.96559565
#  0.96470313  0.96534064  0.96361936  0.96538314]

















