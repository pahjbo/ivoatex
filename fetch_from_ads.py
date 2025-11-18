"""
A script to update docrepo.bib by fetching IVOA records from ADS using the ADS API.

You'll need to get an ADS API key (see
https://github.com/adsabs/adsabs-dev-api) to run this and put it into the
environment variable ADS_TOKEN.

The script will add any new bibcodes found in ADS that are not already in docrepo.bib

In addition the script enhances the information returned from ADS search query by adding the following properties

* url - points to the IVOA landing page for the document (queried from ADS)
* ivoa_docname - the "short" document name/alias (deduced by some heuristics)
* version - the document version
* ids - this is added **only** for the most recent version of a document and is set to "ivoadoc:$ivoa_docname"

The script will report on (but not attempt to change) any differences between existing
entries in the docrepo.bib file and the information returned by ADS - this allows
manual overrides to be made to the docrepo.bib file if necessary.

If successful, it will write BibTeX updates to docrepo.bib (as needed by ivoatex).

Copyright 2020, the GAVO project

This is part of ivoatex, covered by the GPL.  See COPYING for details.
"""

import json
import os,sys
from urllib import parse, request
from urllib.error import HTTPError

import bibtexparser
from bibtexparser.model import Field
import re

API_URL = "https://api.adsabs.harvard.edu/v1/"

try:
    ADS_TOKEN = os.environ["ADS_TOKEN"]
except KeyError:
    sys.exit("No ADS_TOKEN defined.  Get an ADS API key and put it there.")


def do_api_request(_path, _payload=None, **arguments):
    """returns the json-decoded result of an ADS request to path with
    arguments.

    path is relative to API_URL.
    """
    # Yeah, I know, I could save this with requests; but it'd be an
    # extra dependency, and avoiding that is worth a few lines.
    auth_header = {"Authorization": "Bearer %s"%ADS_TOKEN}
    req = request.Request(
        API_URL+_path+"?"+parse.urlencode(arguments),
        data=_payload,
        headers=auth_header)
    f = request.urlopen(req)
    return json.load(f)



def main():
    notere = re.compile("https?://www.ivoa.net/documents/Notes/([^/]+)/")
    stdre = re.compile("https?://www.ivoa.net/documents/([^/]+)/")
    coverre = re.compile("https?://www.ivoa.net/documents/cover/([^/]+)$")
    versionre = re.compile(r"Version\s+(\d\.\d)")
    bibcode_recs = do_api_request("search/query",
        q="bibstem:(ivoa.spec or ivoa.rept)",
        rows="500",
        fl="bibcode")

    bibtex_args = {
        "bibcode": [r["bibcode"] for r in bibcode_recs["response"]["docs"]],}

    bibtex_recs = do_api_request("export/bibtex",
        _payload=json.dumps(bibtex_args).encode("ascii"))
    library = bibtexparser.parse_string(bibtex_recs["export"])

    currentBib = bibtexparser.parse_file("docrepo.bib")

    for bibcode, entry in library.entries_dict.items():
        if bibcode not in currentBib.entries_dict:
            print(f"new entry {bibcode} from ADS")
            resp = do_api_request(f"resolver/{bibcode}/pub_html")
            docURL = resp["link"]
            entry.set_field(Field("url", docURL))
            m = coverre.match(docURL)
            if m:
                ivoa_shortname = m.group(1).split("-")[0]
            else:
                m = notere.match(docURL)
                if m:
                    ivoa_shortname = m.group(1)
                else:
                    m = stdre.match(docURL)
                    if m:
                        ivoa_shortname = m.group(1)
            if ivoa_shortname:
                entry.set_field(Field("ivoa_docname", ivoa_shortname))

            # get the version - can just parse the title of the bibtex entry
            m = versionre.search(entry.fields_dict["title"].value)
            if m:
                thisVersion = m.group(1)
                entry.set_field(Field("version",thisVersion))

                # just check the link
            try:
                f = request.urlopen(docURL)
            except HTTPError as error:
                print(f"{bibcode} - problem accessing {docURL} ",error)
            currentBib.add(entry)
        else:
            # chek for item updates
            for key, field in entry.fields_dict.items():
                if field.value != currentBib.entries_dict[bibcode].fields_dict[key].value:
                    print(f"bibcode {bibcode} : key {key} docrepo.bib val={currentBib.entries_dict[bibcode].fields_dict[key]} ADS val={field}")



    #scan for current version
    currentVersion = {}
    for bibcode, entry in library.entries_dict.items():
        if "version" in entry.fields_dict:
            thisVersion = entry.fields_dict["version"].value
            ivoa_shortname =  entry.fields_dict["ivoa_docname"].value
            if ivoa_shortname in currentVersion:
                if thisVersion > currentVersion[ivoa_shortname]["version"]: # this string comparison will go wrong after version 9
                    currentVersion[ivoa_shortname]["version"] = thisVersion
                    currentVersion[ivoa_shortname]["bibkey"] = bibcode
            else:
                currentVersion[ivoa_shortname] = {"version":thisVersion,"bibkey":bibcode}

        # delete ids field to be reset where appropriate below
        entry.pop("ids")

    for shortname, entry in currentVersion.items():
        currentBib.entries_dict[entry["bibkey"]].set_field(Field("ids",f"ivoadoc:{shortname}")) # set the biblatex citation key alias for the current version of document

    bibtexparser.write_file("docrepo.bib",currentBib)

if __name__=="__main__":
    main()
# vi:sw=4:et:sta
