import { InlineMath, BlockMath } from 'react-katex';
const MathTex = ({ inline, children, className }) => {
  if (inline) {
    return (
      <div className={`${className} inline`}>
        <InlineMath>{children}</InlineMath>
      </div>
    );
  } else {
    return (
      <div className={className}>
        <BlockMath>{children}</BlockMath>
      </div>
    );
  }
};

export default MathTex;
