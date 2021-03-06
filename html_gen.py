#!/usr/bin/python
import sys
import os
import uuid

base_prefix = """
<!DOCTYPE html>
<html>
<head>
<style>
.accordion {
    background-color: #eee;
    color: #444;
    cursor: pointer;
    padding: 18px;
    width: 100%;
    border: none;
    text-align: left;
    outline: none;
    font-size: 15px;
    transition: 0.4s;
}

.active, .accordion:hover {
    background-color: #ccc;
}

.accordion:after {
    content: '+';
    color: #777;
    font-weight: bold;
    float: right;
    margin-left: 5px;
}

.active:after {
    content: "--";
}

.panel {
    padding: 0 18px;
    background-color: white;
    max-height: 0;
    overflow: hidden;
}
.report_obj {
   width: 100%;
   overflow: hidden;
}


</style>
<script src="jquery-3.3.1.min.js"></script>
</head>
<body>

<h2>Recon Summary</h2>
<p>{report_title}</p>
"""



base_suffix = """
<script>

function toggleAcc(acc) {
    acc.classList.toggle("active");
    var panel = acc.nextElementSibling;
    var obj = panel.firstElementChild;
    if (obj){
    if (obj.className=="disabled") {
        console.log("activing element");
        //var d = document.createElement("div");
        //panel.replaceChild(d, obj);

        $(panel).children().first().replaceWith(obj.textContent);

        //d.innerHTML = obj.textContent;
        //$(d).html(obj.textContent);
        
        //obj = d.firstElementChild;
        obj = $(panel).children().first().children().first();
    }
    var doc = obj.contentDocument;
        if(doc) {
            var t = doc.firstElementChild;
        if (t) {
            obj.style.height = t.scrollHeight + "px";
        }
    } else {
        resizePanels(panel);
    }
        
    }
}
function resizePanels(panel) {
    do {
            if (panel.style.maxHeight && panel.previousElementSibling.className == "accordion"){
                      panel.style.maxHeight = null;
            } else {
                        
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
            
             panel = panel.parentElement; 
            
            } while( panel.className == "panel");

}

function resize(obj){

    console.log(obj);
        obj.style.height = obj.scrollHeight + "px";
    panel = obj.parentElement;
    resizePanels(panel);    

}

/*
function resize(obj){
    var doc = obj.contentDocument;
        if(doc) {
            var t = doc.firstElementChild;
                if (t) {
                        obj.style.height = t.scrollHeight + "px";
                }
        }
    console.log(obj);
    panel = $(obj).closest(".panel");
    console.log(panel);
    resizePanels(panel);    
}
*/
</script>
</body>
</html>
"""

base = """
<button class="accordion" onclick="toggleAcc(this)">{}</button>
<div class="panel">
{}
</div>
"""


#base_obj =""" 
#<textarea class ="disabled"><object class="report_obj" type="text/html;base64" onload="resize(this)" data="{}"></object></textarea>
#"""

base_obj =""" 
<textarea class ="disabled">
<div id={} align="left" class="report_obj"></div>
<script>
console.log("Loading element");
tag=document.currentScript;
console.log(tag);

$.get( "{}",
 function(data) {{ 
    console.log("Injecting html..");
        //d = tag.previousSibling;
    console.log(tag);
    //tag.id="here";
        //var d = document.createElement("div");
    //d.class = "report_obj";
    //$(tag).replaceWith(d);
    //console.log("impossible");
    d = $("#{}")[0];
    console.log(d);
    $(d).html(data);
    //console.log(d);
    console.log("Resizing");
    resize(d);
  }});
</script>


</textarea>
"""
# Note: literal curly braces above are doubled so Python accepts it

def makeAccObject(dir, filename):
    target_id = uuid.uuid4()
    obj = base_obj.format(target_id, os.path.join(dir,filename), target_id)
    return base.format(filename, obj)

def wrapAccObjects(target, objs):
    return base.format(target, "\n".join(objs))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "Usage: html_gen.py <hosts_file> <output_file> <report_title>"
        print("Directories named like 0.0.0.0 must exist already and contain data")
        sys.exit(0)
    
    print("Building {} Report".format(sys.argv[3]))
    print("For hosts: {}".format(sys.argv[1]))

    hosts = []
    with open(sys.argv[1], 'r') as hosts_file:
        hosts = hosts_file.read().splitlines()


    reports = []
    dirs = next(os.walk(os.getcwd()))[1]

    dirs = [d for d in dirs if len(d.split('.')) == 4 and d in hosts]
    dirs.sort( key=lambda s: map(int, s.split('.')))

    for dir in dirs:        
        print("\nGenerating report for {}".format(dir))
        objs = []
        (dirpath, dirnames, files) = next(os.walk(dir))
        for category in dirnames:
            cat_objs = []
            print("\tGenerating report for category {}".format(category))
            cat_path = os.path.join(dir,category)
            for file in next(os.walk(cat_path))[2]:
                if not file.startswith('.'):
                    print("\t\tGenerating object {}".format(file))
                    cat_objs.append(makeAccObject(cat_path, file))
            print("\tFinalizing report for {}".format(category))
            if cat_objs:
                objs.append(wrapAccObjects(category, cat_objs)) 
        
        for file in files:
            if not file.startswith('.'):
                print("\tGenerating object {}".format(file))
                objs.append(makeAccObject(dir, file))
        print("Finalizing report for {}".format(dir))
        reports.append(wrapAccObjects(dir, objs))
    print("Writing Final Report...")
    try:
        with open(sys.argv[2], 'w') as out:
            out.write("{}{}{}".format(
                base_prefix.replace('{report_title}', sys.argv[3], 1),
                '\n'.join(reports), 
                base_suffix
                )
            )
        print("Done! {} Report written to {}".format(sys.argv[3], sys.argv[2]))
    except Exception as e:
        print(e)
