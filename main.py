'''

'''
import re, sys,pandas
from bs4 import BeautifulSoup

CIKM_EMAIL_ADDRESS= ""
FIRST_EMAIL_TEMPLATE='''
Dear {},

Thank you for attending CIKM2034 and we hope you have enjoyed it!

As you know, this year CIKM has piloted a novel 'online delivery' mode: we given each registered \
attendee an opportunity to request an additional online presentation for the papers they may be interested in, \
and we ask authors to be prepared to liaise with their interested audience to arrange a separate \
session for this after the conference. We believe this is a mutually beneficial process and \
more effective communication as it creates a dedicated platform for you and your audience, who is \
committed to learn more about your work.

We have gathered interests for your paper:

{}, {}

, and your audience who expressed interests in attending your online presentation includes:
{}

Here we ask you to please get in touch with your audience and endeavour to arrange an online presentation/meet-up \
at a time and using a platform that you find most appropriate. Please do get in touch with the organising committee at \
{} if you have any questions.

Please note that we cannot arrange this for you and your audience. However, we are happy to assist you in any ways that we can.

Kind regards

CIKM online delivery team
(Ziqi Zhang, Xingyi Song, Judita Preiss, Monica Paramita, Oliver, Jordan)
'''

SECOND_EMAIL_TEMPLATE='''
Dear {},

(Kindly note this message is also copied to all authors of the related paper)

We have previously contacted you regarding arranging an online presentation with your interested audience for your work:

{}, {}

However, we understand that your audience has attempted to contact you but to no avail. Can we ask you to please \
kindly get in touch with them to arrange a separate time and platform for delivering your online presentation? \
We believe this is a mutually beneficial process and \
more effective communication as it creates a dedicated platform for you and your audience, who is \
committed to learn more about your work. For more information about this novel 'online presentation' format we are \
piloting this year, please visit our CIKM website.

Once againm, here is your audience list who expressed interests in attending your online presentation:

{}

Please note that we cannot arrange this for you and your audience. However, we are happy to assist you in any ways that we can.

Kind regards

CIKM online delivery team
(Ziqi Zhang, Xingyi Song, Judita Preiss, Monica Paramita, Oliver, Jordan)
'''


EXCLUDES=[1790, 2498]

def read_gform_signups(csv_file):
    # Use a breakpoint in the code line below to debug your script.
    audience_signups={}
    paper_signups ={}

    data = pandas.read_csv(csv_file, header=0)
    for i, row in data.iterrows():
        email  =row[2].strip()
        name = row[1].strip()
        affiliation = row[3].strip()
        papers=re.sub(r'[^a-zA-Z0-9]', ',', row[3].strip()).split(',')
        valid_paper_ids=set()
        for p in papers:
            try:
                id = int(p)
                valid_paper_ids.add(id)
            except:
                pass

        existing_req_of_delegate=audience_signups.get(email,{})
        if len(existing_req_of_delegate)==0:
            existing_req_of_delegate['email']=email
            existing_req_of_delegate['name']=name
            existing_req_of_delegate['affiliation']=affiliation
            existing_req_of_delegate['papers']=set()
        existing_req_of_delegate['papers'].update(valid_paper_ids)
        audience_signups[email]=existing_req_of_delegate

        for paper in valid_paper_ids:
            existing_audience=paper_signups.get(paper, set())
            existing_audience.add(email)
            paper_signups[paper]=existing_audience

    return audience_signups, paper_signups

def read_detailed_xml(xml_file):
    with open(xml_file, 'r') as file:
        xml_content = file.read()
        soup = BeautifulSoup(xml_content, 'lxml')
        # most content is located in a 'table' block
        found = soup.find_all('submission_record')
        count=1
        papers={}
        for f in found:
            print("processing {}/{}".format(count, len(found)))
            count+=1
            id = f.find_next('sheridan_acm_id').text
            title=f.find_next('title').text
            for i in range(0, len(id)):
                if id[i].isdigit():
                    id=id[i:].strip()
                    try:
                        id=int(id)
                    except:
                        pass
                    break

            #contact_author_email
            email_contact=f.find_next('contact_author_email').text

            #authors
            f_authors = f.find_next('authors').find_all("author")
            author_lookup={}

            for f_a in f_authors:
                fname = f_a.find_next('first_name').text
                lname = f_a.find_next('last_name').text
                email = f_a.find_next('email_address').text
                author_lookup[email]=(fname,lname)
            #authors > author > first_name, last_name, email_address
            papers[id]={
                "title":title,
                "email_contact":email_contact,
                "authors":author_lookup
            }
        return papers

def read_accepted_brief(csv_file):
    acceptable_format=["CIKM'23 Short Papers",
                       "CIKM'23 Demo Papers",
                       "CIKM'23 Resource Papers",
                       "CIKM'23 Long/Full Papers",
                       "CIKM'23 Applied Research Papers"]
    data = pandas.read_csv(csv_file, header=0)
    rs={}
    for i, row in data.iterrows():
        format = row[1]
        if format not in acceptable_format:
            print("format of {} is not eligible".format(format))
        rs[int(row[0])] = row
    return rs

def match(audience_signups:dict, paper_signups:dict, papers_detail:dict, papers_brief:dict, out_folder):
    count=1
    for paper, audience_emails in paper_signups.items():
        print("paper {}, {}/{}".format(paper, count, len(paper_signups)))
        count+=1
        if paper not in papers_brief.keys():
            print("This paper is not an accepted one, skipped.")
            continue
        expressed_interests=""
        cc_emails = ','.join(audience_emails)
        for to_e in audience_emails:
            audience_data = audience_signups[to_e]
            expressed_interests+='- '+to_e+", "+audience_data['name']+" from "+audience_data['affiliation']+"\n"
        subject_line = 'CIKM online presentation requests'
        paper_data = papers_detail.get(paper)
        contact_email = paper_data['email_contact']
        contact_author = paper_data['authors'][contact_email][0]+" "+paper_data['authors'][contact_email][1]
        paper_title=paper_data['title']

        #FIRST email
        with open(out_folder+"/{}_email1.txt".format(paper),'w') as file:
            msg = FIRST_EMAIL_TEMPLATE.format(
                contact_author,
                paper ,paper_title,
                expressed_interests, CIKM_EMAIL_ADDRESS
            )
            file.write("TO: {}\n".format(contact_email))
            file.write("CC: {}\n".format(cc_emails))
            file.write("Subject: {}\n".format(subject_line))
            file.write("Message:\n{}".format(msg))

        #SECOND email
        subject_line = "ATTENTION - second request: your CIKM online presentation"
        cc_emails = []
        for au in paper_data['authors']:
            cc_emails.append(au)
        cc_emails.extend(audience_emails)
        cc_emails=','.join(cc_emails)
        with open(out_folder+"/{}_email2.txt".format(paper),'w') as file:
            msg = SECOND_EMAIL_TEMPLATE.format(
                contact_author,
                paper ,paper_title,
                expressed_interests
            )
            file.write("TO: {}\n".format(contact_email))
            file.write("CC: {}\n".format(cc_emails))
            file.write("Subject: {}\n".format(subject_line))
            file.write("Message:\n{}".format(msg))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    papers_detail=read_detailed_xml(sys.argv[1])
    papers_brief = read_accepted_brief(sys.argv[2])
    audience_signup, papers_signup =read_gform_signups(sys.argv[3])
    match(audience_signup, papers_signup, papers_detail, papers_brief, sys.argv[4])
    #read signup datasheet

    #for each signup,
        #for each indicated paper

    exit(0)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
