import { useState } from 'react';
import { Layout, FlexRow, FlexCol, FlexCenter, FormField, Math, Navbar } from '../../components';

// Form fields icons

const depsIconClassName = 'fas fa-bolt';
const urlIconClassName = 'fas fa-link';
const jobIconClassName = 'fas fa-bars';
const nodesIconClassName = 'fas fa-cloud';

const Form = ({ setActiveField }) => {
  return (
    <form className="w-full h-full">
      <FlexCol between className="w-full h-full">
        <FlexRow responsive media="md" className="space-y-1 md:space-y-0 md:space-x-5">
          <FormField label="Job name" inputName="job_name" setActiveField={setActiveField} />
          <FormField
            label="Max N° nodes"
            inputName="max_nodes"
            inputType="number"
            setActiveField={setActiveField}
            minNumber={1}
          />
        </FlexRow>
        <FormField
          label="Tempered distribution family"
          inputName="tempered_distribution_family"
          hasDropdown
          setActiveField={setActiveField}
          disabled
          defaultValue="Boltzman"
        />
        <FlexRow responsive media="md" className="space-y-1 md:space-y-0 md:space-x-5">
          <FormField
            label="Beta min"
            inputName="minimum_beta"
            inputType="number"
            setActiveField={setActiveField}
            minNumber={0}
            maxNumber={1}
            stepNumber={0.1}
          />
          <FormField
            label="Initial schedule beta ratio"
            inputName="initial_schedule_beta_ratio"
            inputType="text"
            setActiveField={setActiveField}
          />
        </FlexRow>
        <FormField
          label="Probability definition"
          inputName="probability_definition"
          inputType="url"
          setActiveField={setActiveField}
        />
        <FormField
          label="Dependencies"
          inputName="dependencies"
          inputType="text"
          setActiveField={setActiveField}
          className="mb-5"
        />

        <FlexCenter>
          <input
            type="submit"
            value="Submit"
            className={
              'w-52 px-6 pt-3 pb-4 text-base text-center bg-purple-700  ' +
              ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
            }
          />
        </FlexCenter>
      </FlexCol>
    </form>
  );
};

const FieldDescription = ({ children, name, activeField, icon, math }) => (
  <div
    className={`${
      activeField === name ? 'text-blue-400' : ''
    } transition duration-200 my-1 lg:my-0`}
  >
    {icon && <i className={`${icon} mr-5`}></i>}
    {math && (
      <Math inline className="mr-5">
        {math}
      </Math>
    )}
    {children}
  </div>
);

const Descs = ({ activeField }) => {
  return (
    <FlexCol between className="w-full h-full">
      <FieldDescription activeField={activeField} name="job_name" icon={jobIconClassName}>
        Job name: a unique key id for your job.
      </FieldDescription>
      <FieldDescription activeField={activeField} name="max_nodes" icon={nodesIconClassName}>
        Max N° nodes: maximum number of compute nodes to use. Specifics of the environment in which
        these are created is configured on the scheduler itself
      </FieldDescription>
      <FieldDescription
        activeField={activeField}
        name="tempered_distribution_family"
        math="\{\mathbb{P}\}"
      >
        Tempered distribution family: the family of tempered distributions to use. For now, the only
        valid value is "Boltzman"
      </FieldDescription>
      <FieldDescription activeField={activeField} name="minimum_beta" math="\beta_{min}">
        Beta min: the minimum inverse temperature (beta) which determines the flatness of the
        flattest distribution
      </FieldDescription>
      <FieldDescription activeField={activeField} name="initial_schedule_beta_ratio" math="\alpha">
        Initial schedule beta ratio: the ratio defining (approximately) the geometric progression
      </FieldDescription>
      <FieldDescription
        activeField={activeField}
        name="probability_definition"
        icon={urlIconClassName}
      >
        Probability definition: URL to archive including importable Python module providing the log
        probability
      </FieldDescription>
      <FieldDescription activeField={activeField} name="dependencies" icon={depsIconClassName}>
        Dependencies: list of dependencies to install on compute nodes
      </FieldDescription>
    </FlexCol>
  );
};

export default function Job() {
  const [activeField, setActiveField] = useState('other');

  return (
    <Layout>
      <FlexCol
        between
        className="px-5 text-white md:px-20 bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body"
      >
        <Navbar />
        <FlexCenter className="w-full h-full py-5 md:py-20">
          <FlexCol center className="w-full h-full">
            <div className="mb-10 text-2xl md:text-5xl lg:text-6xl">
              Run a sampling task
              <i className="ml-3 fas fa-rocket"></i>
            </div>
            <div className="w-full mb-20 text-base md:text-xl lg:w-2/3 md:text-justify">
              Every sampling task is called a <em>job</em>. Every job is specified through several
              attributes. After a job is submitted, the user gets a link to a cloud bucket, which
              contains the samples, sampling statistics such as acceptance rates and an estimate of
              the density of states.
            </div>
            <FlexRow
              between
              responsive
              media="lg"
              className="w-full lg:px-20 lg:h-3/5 lg:space-x-20"
            >
              <FlexCenter className="flex-grow mb-10 lg:py-10 h-96 md:h-80 lg:h-full lg:mb-0">
                <Form
                  setActiveField={setActiveField}
                  clearActiveField={() => setActiveField('other')}
                />
              </FlexCenter>
              <FlexCenter className="w-full p-5 bg-gray-700 md:p-10 lg:w-1/2 lg:h-full rounded-xl">
                <Descs activeField={activeField} />
              </FlexCenter>
            </FlexRow>
          </FlexCol>
        </FlexCenter>
      </FlexCol>
    </Layout>
  );
}
