"""https://graph.facebook.com/v2.0/me?fields=location&access_token=CAAKIicbi6tYBADV2SqujnqfotIZChOKqgEZBMNZCiGOiN2RxtW4uhG2wiMUnbKcsTJcXan86ycCnfxZAVD8FZBtt1SvCH8RHdkk9lZAPutA3Epjy3lp8wERAZCKvmPRJhH2u4l7eerI5G5wcnZBfceoUYQoUaovStnWjjsZCTmWitnltiMr1ethVqxZAMSW1I1kcgrbVRuX90jnQZDZD

://graph.facebook.com/v2.0/search?q=coffee&type=place&center=39.6636963,20.851343300948674&distance=1000&access_token=CAAKIicbi6tYBADV2SqujnqfotIZChOKqgEZBMNZCiGOiN2RxtW4uhG2wiMUnbKcsTJcXan86ycCnfxZAVD8FZBtt1SvCH8RHdkk9lZAPutA3Epjy3lp8wERAZCKvmPRJhH2u4l7eerI5G5wcnZBfceoUYQoUaovStnWjjsZCTmWitnltiMr1ethVqxZAMSW1I1kcgrbVRuX90jnQZDZD
"""
import requests
import json
def fql(query,token):
	""" returns a json response of the specific query"""
	therequest="https://graph.facebook.com/v2.0/"+query+"&access_token="+token
	return json.loads(requests.request("GET",therequest).text)

	
