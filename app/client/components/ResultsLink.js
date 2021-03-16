const ResultsLink = ({ signed_url }) => (
  <a
    download
    href={signed_url}
    className="w-32 py-1 text-center text-white bg-green-600 rounded-lg cursor-pointer lg:transition lg:duration-100 hover:bg-green-700"
  >
    Download results
  </a>
);
export default ResultsLink;
