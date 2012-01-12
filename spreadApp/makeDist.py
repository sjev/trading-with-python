from distutils.core import setup
import py2exe

manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

RT_MANIFEST = 24
import matplotlib


opts = {
				'py2exe': {
				"compressed": 1,
				"bundle_files" : 3,
				"includes" : ["sip",
							"matplotlib.backends",
                            "matplotlib.backends.backend_qt4agg",
                            "pylab", "numpy",
                            "matplotlib.backends.backend_tkagg"],
                'excludes': ['_gtkagg', '_tkagg', '_agg2',
                            '_cairo', '_cocoaagg',
                            '_fltkagg', '_gtk', '_gtkcairo', ],
                'dll_excludes': ['libgdk-win32-2.0-0.dll',
                            'libgobject-2.0-0.dll']

              }
       }



setup(name="triton",
	  version = "0.1",
	  scripts=["spreadScanner.pyw"],
	  windows=[{"script": "spreadScanner.pyw"}], 
	  options=opts,
	  data_files=matplotlib.get_py2exe_datafiles(),	
	  other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="spreadDetective"))],
	  zipfile = None)  