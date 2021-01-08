const FlexCol = ({
  children,
  className,
  style,
  center,
  between,
  onMouseEnter,
  onMouseLeave,
  onClick,
  responsive,
  media,
}) => {
  return (
    <div
      className={`flex
      ${responsive ? `flex-row ${media ? media : 'lg'}:flex-col` : 'flex-col'}
      ${center ? 'justify-center' : ''}
      ${between ? 'justify-between' : ''}
      ${className}
	    `}
      style={style}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

const FlexRow = ({
  children,
  className,
  style,
  center,
  between,
  onMouseEnter,
  onMouseLeave,
  responsive,
  media,
  onClick,
}) => {
  return (
    <div
      className={`flex flex-row
      ${responsive ? `flex-col ${media ? media : 'lg'}:flex-row` : 'flex-row'}
      ${center ? 'justify-center' : ''}
      ${between ? 'justify-between' : ''}
      ${className}
	  `}
      style={style}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

const FlexCenter = ({ children, className, style }) => {
  return (
    <div
      className={`flex flex-row items-center justify-center
	  ${className}
	  `}
      style={style}
    >
      {children}
    </div>
  );
};

export { FlexCol, FlexRow, FlexCenter };
