const ResultsLink = ({ signed_url }) => {
  if (signed_url) {
    return (
      <a
        download
        href={signed_url}
        className="w-32 py-1 text-center text-white bg-green-600 rounded-lg cursor-pointer lg:transition lg:duration-100 hover:bg-green-700"
      >
        download
      </a>
    );
  } else {
    return <></>;
  }
};
export default ResultsLink;
