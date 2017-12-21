from distutils.core import setup
import py2exe

options = dict(excludes=['_ssl',  # Exclude _ssl
                                 'pyreadline', 'difflib', 'doctest', 'locale',
                                 'optparse', 'pickle', 'calendar', 'pbd', 'unittest', 'inspect'],  # Exclude standard library
    dll_excludes=['msvcr71.dll', 'w9xpopen.exe',
                                     'API-MS-Win-Core-LocalRegistry-L1-1-0.dll',
                                     'API-MS-Win-Core-ProcessThreads-L1-1-0.dll',
                                     'API-MS-Win-Security-Base-L1-1-0.dll',
                                     'KERNELBASE.dll',
                                     'POWRPROF.dll',
                                     ],
    bundle_files = 2,
    optimize = 2,
    ascii=True,
    includes = ["sip", 'Phonon']
)
setup(windows=[{"script" : "PyIpChanger.py",'uac_info': "requireAdministrator"}], options = {'py2exe': options}, zipfile = None)
