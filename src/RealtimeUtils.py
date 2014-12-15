import sys
import os
import zipfile
import zlib
import urllib

from robot import utils
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
from robot.version import get_version

class RealtimeUtils(object):
    """Some util functions specific to realtime
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = get_version()

    def embed_log_file(self, url, name="realtime"):
        response = urllib.urlopen(url)
        content = response.read()
        path = self._save_datafile(name, content)
        self._link_file(path)
        return path

    def _save_datafile(self, name, data):
        path = self._get_path(name, ".zip")
        zf = zipfile.ZipFile(path, mode='w', compression=zipfile.ZIP_DEFLATED)
        try:
            zf.writestr(name + '.log', data)
        finally:
            zf.close()
        return path

    def _get_path(self, basename, ext=".log"):
        directory = self._norm_path(self._log_dir)
        index = 0
        while True:
            index += 1
            path = os.path.join(directory, "%s_%d%s" % (basename, index, ext))
            if not os.path.exists(path):
                return path

    def _link_file(self, path):
        link = utils.get_link_path(path, self._log_dir)
        logger.info("Saved to '<a href=\"%s\">%s</a>'." % (link, path), html=True)
                    
    def _norm_path(self, path):
        if not path:
            return path
        return os.path.normpath(path.replace('/', os.sep))

    @property
    def _log_dir(self):
        variables = BuiltIn().get_variables()
        outdir = variables['${OUTPUTDIR}']
        log = variables['${LOGFILE}']
        log = os.path.dirname(log) if log != 'NONE' else '.'
        return self._norm_path(os.path.join(outdir, log))


