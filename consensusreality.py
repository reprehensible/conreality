from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
import os
from google.appengine.ext.webapp import template
import cgi
from google.appengine.ext import db
import random

class Fact(db.Model):
	txt = db.StringProperty(required=True)
	truth = db.FloatProperty(required=True)
	importance = db.FloatProperty(required=True)
	factness = db.FloatProperty(required=True)
	magnitude = db.IntegerProperty(required=True)
	originator = db.UserProperty(required=True)

class UserData(db.Model):
	user = db.UserProperty(required=True)
	voted_on = db.StringListProperty()

class Vote(db.Model):
	voter = db.UserProperty(required=True)
	fact = db.ReferenceProperty(Fact)

	truth = db.IntegerProperty(required=True)
	importance = db.IntegerProperty(required=True)
	factness = db.IntegerProperty(required=True)
	magnitude = db.IntegerProperty(required=True)

class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		self.show_page(user)

	def post(self):
		user = users.get_current_user()
		if user:
			self.process(user)
			self.redirect('/')
		else:
			self.redirect(users.create_login_url(self.request.uri))

	def process(self, user):
		txt = self.request.get('fact_txt')
		v_fact_id = self.request.get('v_fact_id')
		v_factness = self.request.get('v_factness')
		v_truth = self.request.get('v_truth')
		v_importance = self.request.get('v_importance')

		if txt and (len(txt) < 101):
			new_fact = Fact(txt=txt, truth=0.0, importance=0.0, magnitude=0, factness=0.0, originator=user)
			new_fact.put()
		if v_factness != '' and v_truth != '' and v_importance != '' and v_fact_id != '':
			q = db.GqlQuery("SELECT * FROM UserData WHERE user = :1", user)
			userdata = q.get()
			if not userdata:
				userdata = UserData(user=user)

			fact = db.get(db.Key(v_fact_id))
			if userdata.voted_on.count(str(fact.key())) < 1:
				mag = fact.magnitude
				fact.truth = self.newval(fact.truth, mag, float(v_truth))
				fact.factness = self.newval(fact.factness, mag, float(v_factness))
				fact.importance = self.newval(fact.importance, mag, float(v_importance))
				fact.magnitude = fact.magnitude + 1
				fact.put()
				userdata.voted_on.append(str(fact.key()))
				userdata.put()

	def newval(self, thing, magnitude, plus):
		return ((thing * magnitude) + plus) / (magnitude + 1)

	def show_page(self, user):
		q = Fact.all()
		q.order('-factness')
		q.order('-truth')
		q.order('-importance')
		q.order('-magnitude')
		
		some_facts = q.fetch(20)
		show_new = False
		show_vote = False
		v_fact = None
		if user:
			show_new = True
			q = db.GqlQuery("select * from Fact where magnitude < 200")
			v_facts = q.fetch(500)
			if len(v_facts) > 0:
				show_vote = True
				v_fact = random.choice(v_facts)
	
		template_values = {
			'some_facts': some_facts,
			'show_new': show_new,
			'show_vote': show_vote,
			'v_fact': v_fact,
			'login_url': users.create_login_url(self.request.uri)
		}
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))

class Detail(webapp.RequestHandler):
	def get(self):
		fact_id = self.request.get('id')
		if (fact_id):
			fact = Fact.get(db.Key(fact_id))
			template_values = { 'fact': fact }
			path = os.path.join(os.path.dirname(__file__), 'detail.html')
			self.response.out.write(template.render(path, template_values))
		

application = webapp.WSGIApplication(
	[('/', MainPage), ('/detail', Detail)],
	debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
