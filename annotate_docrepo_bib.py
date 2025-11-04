"""
A script to try to infer the IVOA document metadata from bibtex entry fetched from ADS, and write it back

"""
from urllib.error import HTTPError

import bibtexparser
from bibtexparser.model import Field
import re

def main():
    library = bibtexparser.parse_file("docrepo.bib")
    notere = re.compile("https?://www.ivoa.net/documents/Notes/([^/]+)/")
    stdre = re.compile("https?://www.ivoa.net/documents/([^/]+)/")
    coverre = re.compile("https?://www.ivoa.net/documents/cover/([^/]+)$")
    versionre = re.compile(r"Version\s+(\d\.\d)")
    currentVersion = {}
    for bibcode, entry in library.entries_dict.items():
        docURL = entry.fields_dict["url"].value
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

        # get the version - could just parse the title of the bibtex entry
        m = versionre.search(entry.fields_dict["title"].value)
        if m:
            thisVersion = m.group(1)
            entry.set_field(Field("version",thisVersion))
            if ivoa_shortname in currentVersion:
                if thisVersion > currentVersion[ivoa_shortname]["version"]: # this string comparison will go wrong after version 9
                    currentVersion[ivoa_shortname]["version"] = thisVersion
                    currentVersion[ivoa_shortname]["bibkey"] = bibcode
            else:
                currentVersion[ivoa_shortname] = {"version":thisVersion,"bibkey":bibcode}

    for shortname, entry in currentVersion.items():
        library.entries_dict[entry["bibkey"]].set_field(Field("ids",f"ivoadoc:{shortname}")) # set the biblatex citation key alias for the current version of document

    bibtexparser.write_file("docrepo.bib",library)


if __name__=="__main__":
    main()