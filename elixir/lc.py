import argparse
import logging

from elixir import feedstock

logger = logging.getLogger(__name__)

def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    
    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)

    return logger

def main(pid, source_dir='.', deposit_dir=None):

    logger.info('Starting to pack a document')

    if feedstock.is_valid_pid(pid):
        xml = feedstock.loadXML(pid)
        raw_data = feedstock.load_rawdata(pid)
        article = feedstock.Article(pid, xml, raw_data, source_dir, deposit_dir)

        article.wrap_document()


def argp():
    parser = argparse.ArgumentParser(
        description="Create a article package from the legacy data")

    parser.add_argument(
        '--pid',
        '-p',
        default=None,
        help='Document ID, must be the PID number'
    )

    parser.add_argument(
        '--source_dir',
        '-s',
        default='.',
        help='Source directory where the pdf, images and html\'s cold be fetched'
    )

    parser.add_argument(
        '--logging_file',
        '-o',
        default=None,
        help='File to record all logging data, if None the log will be send to the standard out'
    )

    parser.add_argument(
        '--logging_level',
        '-l',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='File to record all logging data, if None the log will be send to the standard out'
    )

    parser.add_argument(
        '--deposit_dir',
        '-d',
        default=None,
        help='Directory to receive the packages'
    )

    args = parser.parse_args()

    _config_logging(args.logging_level, args.logging_file)

    main(
        args.pid,
        source_dir=args.source_dir,
        deposit_dir=args.deposit_dir
    )

if __name__ == "__main__":

    argp()
