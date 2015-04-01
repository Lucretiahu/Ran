#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import time
import random
import json

import tornado.httpserver
import tornado.httpclient
import tornado.web
import tornado.options
from tornado.options import define, options, parse_command_line

import db

define('port', default=4812, help='given port', type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        sections = db.get_sections()
        uid = self.get_secure_cookie('user')
        print 'uid: ', uid
        forum = db.get_forum()
        allPosts = db.get_all_posts_split_by_section()
        wealthList = db.get_wealth_list()
        if uid:
            user = db.get_user(uid)
        else:
            user = {}
        self.render(
                't_home.html', title='Ran - Home',
                user=user, forum=forum, sections=sections,
                allPosts=allPosts, wealthList=wealthList,
                )

    def post(self):
        pass

class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        adminId = self.get_secure_cookie('admin')
        forum = db.get_forum()
        allUsers = db.get_all_users()
        allPosts = db.get_all_posts()
        allReplys = db.get_all_replys()
        wealthList = db.get_wealth_list()
        cUser = db.get_admin(adminId)
        self.render(
                't_admin.html', title='Ran - Admin',
                allUsers=allUsers, forum=forum, allReplys=allReplys,
                allPosts=allPosts, wealthList=wealthList, cUser=cUser,
                )


class NewHandler(tornado.web.RequestHandler):
    def get(self):
        sections = db.get_sections()
        forum = db.get_forum()
        wealthList = db.get_wealth_list()
        uid = self.get_secure_cookie('user')
        if uid:
            user = db.get_user(uid)
        self.render(
                't_new.html', title='Ran - New',
                sections=sections, forum=forum, user=user,
                wealthList=wealthList,
                )
        pass

    def post(self):
        timeStamp = time.strftime('%Y%m%d%H%m%S', time.localtime())
        uid = int(self.get_secure_cookie('user'))
        title = self.get_argument('title')
        content = self.get_argument('content')
        sectionName = self.get_argument('sectionName')
        att = self.request.files.get('att')
        res = db.new_post(uid, title, content, sectionName, att, timeStamp)
        if res == 1:
            self.redirect('/home')
        else:
            self.redirect('/new')

class SignInHandler(tornado.web.RequestHandler):
    def get(self):
        sections = db.get_sections()
        action = self.get_argument('action', None)
        warning = self.get_argument('warning', None)
        if action == 'logout':
            self.set_secure_cookie('user', '')
        self.render('t_signin.html', title='Ran - Sign In', sections=sections, warning=warning)

    def post(self):
        pass

class SignUpHandler(tornado.web.RequestHandler):
    def get(self):
        sections = db.get_sections()
        self.render('t_signup.html', title='Ran - Sign Up', sections=sections)

    def post(self):
        email =  self.get_argument('email')
        account =  self.get_argument('account')
        pwd =  self.get_argument('pwd1')
        res, uid = db.new_user(email, account, pwd)
        if res == 1:
            self.set_secure_cookie('user', str(uid))
            self.redirect('/home')
        else:
            self.redirect('/signup')

class TopicHandler(tornado.web.RequestHandler):
    def get(self):
        pid = self.get_argument('pid')
        uid = self.get_secure_cookie('user')
        user = db.get_user(uid)
        replys = db.get_replys(pid)
        post = db.get_post_topic(pid)
        att = db.get_att(pid)
        forum = db.get_forum()
        wealthList = db.get_wealth_list()
        self.render(
                't_topic.html', title='Ran - Topic',
                user=user, forum=forum, replys=replys,
                post=post, wealthList=wealthList, att=att,
                )

    def post(self):
        uid = self.get_secure_cookie('user')
        timeStamp = time.strftime('%Y%m%d%H%m%S', time.localtime())
        content = self.get_argument('content')
        sectionName = self.get_argument('section')
        tPid = self.get_argument('tPid')
        res = new_reply(uid, timeStamp, content, sectionName, tPid)
        if res == 1:
            self.redirect('/topic?pid=%d' % int(tPid))
        else:
            self.redirect('/home')


class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        uid = self.get_secure_cookie('user')
        user = db.get_user(uid)
        sections = db.get_sections()
        forum = db.get_forum()
        wealthList = db.get_wealth_list()
        warning = self.get_argument('warning', None)
        self.render(
                't_config.html', title='Ran - Config',
                user=user, setions=sections, forum=forum,
                warning=warning, wealthList=wealthList,
                )

    def post(self):
        uid = int(self.get_secure_cookie('user'))
        action = self.get_argument('action')
        if action == 'info':
            address = self.get_argument('address')
            account = self.get_argument('account')
            res = update_info(address, account, uid)
        elif action == 'icon':
            icon = self.request.files.get('icon')
            icon = icon[0]
            res = update_icon(uid, icon)
        elif action == 'pwd':
            newPwd = self.get_argument('new')
            res = update_pwd(newPwd, uid)
        if res == 1:
            warning = 'updata success'
        else:
            warning = 'update fail'
        self.redirect('/config?warning=%s' % warning)

class DBHandler(tornado.web.RequestHandler):
    def get(self):
        action = self.get_argument('action')
        if action == 'ck_mail':
            param = self.get_argument('param')
            res = db.signup_check('email', param)
        elif action == 'ck_pwd':
            param = self.get_argument('param')
            res = db.pwd_check(param)
        elif action == 'buy_att':
            buid = self.get_argument('buid')
            suid = self.get_argument('suid')
            cost = self.get_argument('cost')
            res = db.buy_att(buid, suid, cost)
        elif action == 'del_user':
            uid = self.get_argument('uid')
            res = db.del_user(uid)
        self.write(res)

    def post(self):
        mail = self.get_argument('mail')
        pwd = self.get_argument('pwd')
        flag, res = db.signin_check(mail, pwd)
        if flag == 'T':
            if not self.get_secure_cookie('user'):
                uid = res[0][0]
                self.set_secure_cookie('user', str(uid))
            self.redirect('/home')
        elif flag == 'F':
            self.redirect('/signin?warning=Invalid Account or Password')
        elif flag == 'T-admin':
            if not self.get_secure_cookie('admin'):
                adminId = res[0][0]
                self.set_secure_cookie('admin', str(adminId))
            self.redirect('/admin')

class MemberHandler(tornado.web.RequestHandler):
    def get(self, part, uid):
        user = db.get_user(uid)
        cUid = self.get_secure_cookie('user')
        cUser = db.get_user(cUid)
        posts = db.get_post_by_id(uid)
        replys = db.get_reply_by_id(uid)
        if part == 'reply':
            posts = []
        elif part == 'post':
            replys = []
        self.render(
                't_member.html', title='Ran - Member',
                user=user, replys=replys, posts=posts,
                cUser=cUser,
                )

class SearchHandler(tornado.web.RequestHandler):
    def get(self):
        searchKey = self.get_argument('searchInput')
        cUid = self.get_secure_cookie('user')
        cUser = db.get_user(cUid)
        posts = db.get_post_by_key(searchKey)
        self.render(
                't_search.html', title='Ran - Search',
                posts=posts, cUser=cUser,
                )

class FriendsHandler(tornado.web.RequestHandler):
    def get(self):
        uid = self.get_secure_cookie('user')
        user = db.get_user(uid)
        posts = db.get_friends_post(uid)
        self.render(
                't_friends.html', title='Ran - Friends',
                user=user, posts=posts,
                )


class FollowHandler(tornado.web.RequestHandler):
    def get(self, fid):
        uid = self.get_secure_cookie('user')
        if fid == uid:
            self.write('F')
        else:
            res = db.follow(int(uid), int(fid))
            if res == 1:
                self.write('T')
            else:
                self.write('F')


class DraftHandler(tornado.web.RequestHandler):
    def get(self):
        uid = int(self.get_secure_cookie('user'))
        res = get_draft(uid)
        self.write(res)

    def post(self):
        title = self.get_argument('title')
        content = self.get_argument('content')
        uid = int(self.get_secure_cookie('user'))
        res = new_draft(title, content, udi)
        if res == 1:
            self.write('T')
        else:
            self.write('F')

class PostModule(tornado.web.UIModule):
    def render(self, post):
        return self.render_string('modules/post.html', post=post)

class ReplyModule(tornado.web.UIModule):
    def render(self, reply):
        return self.render_string('modules/reply.html', reply=reply)


def send(url, data):
    client = tornado.httpclient.HTTPClient()
    url = url
    body = data
    headers = {
        'Content-Type': 'application/json',
        'Connection': 'Keep-Alive',
    }
    request = tornado.httpclient.HTTPRequest(
            url,
            method = 'POST',
            body = body,
            headers = headers
            )
    response = client.fetch(request)
    return response

def main():
    parse_command_line()
    settings = {
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
        'template_path': os.path.join(os.path.dirname(__file__), "templates"),
        'cookie_secret': 'QkLMyvr5Q2CNq+wlLX7q5vcGjjx6K0xZjSyvgTds7vY=',
        'ui_modules': {
            'Post': PostModule,
            'Reply': ReplyModule,
        },
        'debug': True
    }
    application = tornado.web.Application([
            (r'/home', MainHandler),
            (r'/new', NewHandler),
            (r'/signin', SignInHandler),
            (r'/signup', SignUpHandler),
            (r'/topic', TopicHandler),
            (r'/config', ConfigHandler),
            (r'/db', DBHandler),
            (r'/member/([a-z]+)/([0-9]+)', MemberHandler),
            (r'/follow/([0-9]+)', FollowHandler),
            (r'/friends', FriendsHandler),
            (r'/draft', DraftHandler),
            (r'/search', SearchHandler),
            (r'/admin', AdminHandler),
            ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
