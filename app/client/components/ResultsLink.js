import { Link } from '../components';

const ResultsLink = ({ signed_url }) => {
    if (signed_url == null) {
	return <span className="w-30"> n/a </span>;
    } else {
	// underline not working ;-(
	return <Link href={`${signed_url}`} style={{ textDecoration: 'underline' }}>
            link
            </Link>
    }
};

export default ResultsLink;
